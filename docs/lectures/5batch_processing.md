---
delivery date:
  - "[[2026-02-13]]"
---

### Online vs offline systems 
---

1. **Services (Online Systems)**
- Wait for client requests.
- Process each request quickly and return a response.
- **Primary performance metric:** Response time (latency).
- **Key requirement:** High availability (must be reachable when needed).
- Example: Web servers, APIs, databases serving live queries.

---

2. **Batch Processing Systems (Offline Systems)**

- Process large volumes of data as jobs.
- Jobs run periodically (e.g., daily) and may take minutes to days.
- No user is waiting for immediate results.
- **Primary performance metric:** Throughput (how much data can be processed in a given time).
- Example: Nightly analytics, report generation, large-scale data transformations.

---

3. **Stream Processing Systems (Near-Real-Time Systems)**
- Continuously consume events and produce outputs.
- Process data shortly after events occur (not waiting for full datasets).
- Lower latency than batch systems.
- Bridge between online and batch processing.
- **Primary focus:** Low-latency processing of continuous data streams.
- Example: Real-time fraud detection, live metrics dashboards.
---

**Core Differences at a Glance**

| System Type | Input Model       | User Waiting? | Main Metric              | Latency  |
| ----------- | ----------------- | ------------- | ------------------------ | -------- |
| Services    | Request-driven    | Yes           | Response time            | Very low |
| Batch       | Fixed dataset     | No            | Throughput               | High     |
| Stream      | Continuous events | Usually no    | Low latency + throughput | Low      |

---
