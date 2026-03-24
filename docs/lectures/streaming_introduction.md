# Foundations of Stream Processing and Event-Driven Architectures

## Prerequisites
- Familiarity with Batch Processing/MapReduce mechanics.
- Understanding of basic networking protocols (TCP/UDP) and flow control.
- Knowledge of disk I/O performance (sequential throughput vs. capacity).

## Objectives

1. **Distinguish between bounded and unbounded data**, identifying why the latter requires moving away from traditional sort-based batching.
2. **Evaluate the trade-offs between direct and broker-based messaging**, specifically regarding latency, durability, and the "online requirement."
3. **Analyze how load balancing across multiple consumers** can inadvertently compromise message ordering and break causal dependencies.
4. **Explain the mechanics of log-based partitioning and offsets**, contrasting them with the destructive read patterns of traditional message brokers.
5. **Calculate disk-based buffering capacities** to determine the retention window of a production stream under peak load.

---

## Batch vs streams

| Aspect                      | Batch Processing                                   | Stream Processing                                   |
| --------------------------- | -------------------------------------------------- | --------------------------------------------------- |
| **Input Nature**            | **Bounded** (finite, known dataset)                | **Unbounded** (continuous, never-ending data)       |
| **Data Arrival**            | Collected first, processed later                   | Processed as it arrives                             |
| **Processing Trigger**      | Runs on complete dataset (e.g., daily/hourly jobs) | Runs continuously (event-by-event or micro-batches) |
| **Latency**                 | High (minutes → hours → days)                      | Low (milliseconds → seconds)                        |
| **Output Timing**           | Produced after full input is processed             | Produced incrementally in real-time                 |
| **Completeness Assumption** | Assumes dataset is complete                        | No notion of “complete” dataset                     |
| **Example Constraint**      | Sorting requires full data before output           | Can process partial/incremental results             |
| **Freshness of Results**    | Delayed (e.g., yesterday’s data today)             | Near real-time updates                              |
| **Use Cases**               | Analytics, reports, indexing, ML training          | Monitoring, fraud detection, real-time dashboards   |
| **Failure Recovery**        | Re-run entire job (recomputable)                   | Requires state management + checkpointing           |
| **Time Handling**           | Artificial time slicing (daily/hourly batches)     | Native time-aware (event time, processing time)     |


--------------------------------------------------------------------------------
We move now from the theoretical definition of "unbounded streams" to the practical engineering unit of information: the **Event**.

## The Anatomy of an Event

In distributed systems, reliability is built upon the foundation of **immutability**. Unlike a traditional database record that is frequently updated or overwritten, an event is a permanent, immutable record of an action. This immutability ensures that once data enters the stream, it remains a stable reference point for all downstream systems, greatly simplifying recovery and auditing.

Technically, an **Event** is a small, self-contained, immutable object. It must contain:

- **A Timestamp:** Indicating exactly when the event occurred (ideally using a time-of-day clock).
- **Encoding:** The data structure, which may be text-based (JSON) or a more efficient binary form.

Why prioritize immutability? In a system where data is mutable, you only see the "current state." If a value is corrupted, the history of how you arrived there is lost. With immutable events, you have a perfect audit trail. If a bug is discovered in your processing logic, you can "replay" the immutable events from the beginning to recreate the correct state.

---
## Messaging Paradigms: Direct vs. Broker-Mediated

Architects must choose how to transport events from producers (GlobalShop web servers) to consumers (inventory or fraud services). This is a strategic trade-off between latency and reliability.

### Direct Messaging

Systems like UDP Multicast, ZeroMQ, or Webhooks allow for fast, point-to-point communication.

- **The Industry Warning:** The primary limitation here is the **Online Requirement**. In direct messaging, both the producer and consumer must be online simultaneously. I must warn you: relying on direct messaging for critical business logic (like GlobalShop's "checkout" events) is incredibly fragile. If the consumer service crashes, the events are lost unless the producer implements complex manual retry logic—which usually fails under pressure.

### Message Brokers

A Message Broker acts as a "database optimized for streams." It is a centralized server where producers write and consumers read. This asynchronicity allows the system to tolerate consumer downtime by buffering messages.

- **Database Parity:** Some brokers even support **Two-Phase Commit protocols (XA/JTA)**. This allows a broker to participate in a distributed transaction, ensuring that a message is only acknowledged if a corresponding database write also succeeds—bringing brokers closer to the consistency guarantees of a database.

### Comparative Analysis: Database vs. Message Broker

|                    |                                |                                       |
| ------------------ | ------------------------------ | ------------------------------------- |
| Feature            | Database                       | Message Broker                        |
| **Data Retention** | Kept until explicitly deleted. | Traditionally deleted after delivery. |
| **Working Set**    | Can be massive (terabytes).    | Assumed to be small (short queues).   |
| **Query Pattern**  | Point-in-time snapshots.       | Notifications of new data (Pub/Sub).  |
| **Transactions**   | Standard (ACID).               | Supported via XA/JTA in some systems. |

--------------------------------------------------------------------------------

## Consumer Patterns: Load Balancing and Fan-out

When multiple consumers interact with GlobalShop’s "Orders" topic, we see two primary patterns:

1. **Load Balancing:** Each message is delivered to exactly one consumer in a group. This is ideal for parallelizing expensive tasks like payment processing.
2. **Fan-out:** Every message is delivered to all consumers. This allows the shipping service and the analytics service to both "tune in" to the same stream independently.

### The Reliability Trap: Acknowledgments and Redelivery

Brokers use **acknowledgments (ACKs)** to ensure no event is lost. If a consumer crashes, the broker redelivers the unacknowledged message to another consumer.

- **The "So What?" Layer (Causal Dependencies):** Consider Figure 11-2. Producer 1 sends m3 and m4. Consumer 2 takes m3 but crashes before acknowledging. Meanwhile, Consumer 1 is processing m4. The broker redelivers m3 to Consumer 1. Now, Consumer 1 processes m4 _then_ m3.
- **The Result:** If m3 was "Payment Successful" and m4 was "Ship Item," the system just tried to ship an item before the payment was confirmed. This reordering breaks **causal dependencies** and can lead to massive operational failures.

--------------------------------------------------------------------------------

## Deep Dive: Log-Based Message Brokers

Log-based brokers (Kafka, Kinesis) bridge the gap between databases and messaging by using an **append-only sequence of records on disk**.

### Partitioning Mechanics

To scale, a Topic is split into **Partitions**. Each partition is a separate file that can be hosted on a different machine. At GlobalShop, we partition by UserID; all events for User 123 go to Partition 0, ensuring they stay in strict chronological order.

### Offset Management

Every message in a partition has a unique **Offset** (a sequence number). The consumer acts as a **database follower**, keeping track of the last offset it read. If it crashes, it restarts from the last recorded offset.

### Head-of-Line Blocking

In a log-based system, we encounter **Head-of-Line Blocking**. Because a partition is read sequentially, if a single "poison pill" message is slow or fails to process, it blocks _all_ subsequent messages in that partition. This is the trade-off for maintaining order; unlike traditional brokers where other consumers can "jump the queue," the log requires you to clear the pipe in order.

--------------------------------------------------------------------------------

## Performance & Engineering Insights: The GlobalShop Scenario

Data engineering is dictated by the "physics" of hardware. Let's apply this to GlobalShop’s infrastructure.


## Common Pitfalls

1. **Event Time vs. Broker Time:** Never use the time the broker received the message for business logic. Always use the timestamp generated at the source.
2. **Global Order Assumption:** Remember, ordering is only guaranteed **within a partition**, not across the entire topic.
3. **Destructive Reads:** Don't assume all brokers act like AMQP. In log-based systems, reading is a non-destructive, repeatable operation.


## Summary

- **Unbounded Data:** Real-world data is a continuous flow; stream processing treats it as such without artificial batch delays.
- **Immutability:** Events are facts. By keeping them immutable, we create a repeatable, recoverable system.
- **Log-Based Storage:** Partitioning and offsets allow us to scale throughput while maintaining a "replayable" history of events.
- **Operational Safety:** The large disk-based buffers of log-based brokers provide a safety net for slow consumers, allowing human intervention before data loss occurs.

## References
1. Chapter 11, Stream Processing: Designing Data Intensive Applications