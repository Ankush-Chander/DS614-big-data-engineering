#!/usr/bin/env python3
"""
event_generator.py
Generates fake streaming events (taxi trip starts) and writes them
to a specified sink: file | socket | redis | rabbitmq | sqs

Usage examples:
    python event_generator.py file --path /tmp/stream_events.jsonl --interval 1 --count 20
    python event_generator.py socket --host localhost --port 9999 --interval 1 --count 20
    python event_generator.py redis --channel taxi_events --interval 1 --count 20
    python event_generator.py rabbitmq --queue taxi_events --interval 0.5 --count 20
    python event_generator.py sqs --queue-url <url> --interval 1 --count 20
"""
import json, time, random, argparse, socket, os, sys
from datetime import datetime

ZONES = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]


def make_event():
    """Generate a single fake taxi trip-start event."""
    return {
        "event_id": random.randint(100000, 999999),
        "timestamp": datetime.now().isoformat(),
        "pickup_zone": random.choice(ZONES),
        "passengers": random.randint(1, 6),
        "fare_estimate": round(random.uniform(5.0, 85.0), 2),
    }


# ── Sink: Append to file ──────────────────────────────────────────────────────
def sink_file(path: str, interval: float, count: int):
    """Append JSON events line-by-line to a file (JSONL format)."""
    with open(path, "a") as f:
        for i in range(count):
            event = make_event()
            f.write(json.dumps(event) + "\n")
            f.flush()
            print(f"  [file] Wrote event {i+1}/{count}")
            time.sleep(interval)


# ── Sink: Unix TCP socket ─────────────────────────────────────────────────────
def sink_socket(host: str, port: int, interval: float, count: int):
    """Send JSON events over a TCP socket, one per line."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        for i in range(count):
            event = make_event()
            s.sendall((json.dumps(event) + "\n").encode())
            print(f"  [socket] Sent event {i+1}/{count}")
            time.sleep(interval)


# ── Sink: Redis Pub/Sub ───────────────────────────────────────────────────────
def sink_redis(channel: str, interval: float, count: int):
    """Publish JSON events to a Redis Pub/Sub channel."""
    import redis
    r = redis.Redis()
    for i in range(count):
        event = make_event()
        r.publish(channel, json.dumps(event))
        print(f"  [redis] Published event {i+1}/{count}")
        time.sleep(interval)


# ── Sink: RabbitMQ ────────────────────────────────────────────────────────────
def sink_rabbitmq(queue: str, interval: float, count: int):
    """Publish JSON events to a RabbitMQ queue."""
    import pika
    conn = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    ch = conn.channel()
    ch.queue_declare(queue=queue)
    for i in range(count):
        event = make_event()
        ch.basic_publish(exchange="", routing_key=queue, body=json.dumps(event))
        print(f"  [rabbitmq] Published event {i+1}/{count}")
        time.sleep(interval)
    conn.close()


# ── Sink: Amazon SQS (LocalStack) ────────────────────────────────────────────
def sink_sqs(queue_url: str, interval: float, count: int):
    """Send JSON events to an Amazon SQS queue (via LocalStack)."""
    import boto3
    sqs = boto3.client(
        "sqs",
        endpoint_url="http://localhost:4566",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    for i in range(count):
        event = make_event()
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(event))
        print(f"  [sqs] Sent event {i+1}/{count}")
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate fake taxi-trip streaming events to various sinks."
    )
    parser.add_argument(
        "sink",
        choices=["file", "socket", "redis", "rabbitmq", "sqs"],
        help="Where to send events",
    )
    parser.add_argument("--path", default="/tmp/stream_events.jsonl",
                        help="File path (for 'file' sink)")
    parser.add_argument("--host", default="localhost",
                        help="Host (for 'socket' sink)")
    parser.add_argument("--port", type=int, default=9999,
                        help="Port (for 'socket' sink)")
    parser.add_argument("--channel", default="taxi_events",
                        help="Redis channel (for 'redis' sink)")
    parser.add_argument("--queue", default="taxi_events",
                        help="Queue name (for 'rabbitmq' sink)")
    parser.add_argument("--queue-url", default="",
                        help="SQS queue URL (for 'sqs' sink)")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Seconds between events (default: 1.0)")
    parser.add_argument("--count", type=int, default=20,
                        help="Number of events to generate (default: 20)")
    args = parser.parse_args()

    print(f"🚀 Starting event generator: sink={args.sink}, "
          f"interval={args.interval}s, count={args.count}")

    if args.sink == "file":
        sink_file(args.path, args.interval, args.count)
    elif args.sink == "socket":
        sink_socket(args.host, args.port, args.interval, args.count)
    elif args.sink == "redis":
        sink_redis(args.channel, args.interval, args.count)
    elif args.sink == "rabbitmq":
        sink_rabbitmq(args.queue, args.interval, args.count)
    elif args.sink == "sqs":
        sink_sqs(args.queue_url, args.interval, args.count)

    print("✅ Event generator finished.")
