# scripts/test_pipeline.py
import os
import json
import sys
from typing import Any, Dict, List
import requests

BASE_URL = os.getenv("PIPELINE_BASE_URL", "http://127.0.0.1:8000")
ENDPOINT = "/run"
URL = BASE_URL.rstrip("/") + ENDPOINT

def call_run(transcript: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"transcript": transcript, "metadata": metadata}
    try:
        resp = requests.post(URL, json=payload, timeout=90)
        print(f"HTTP {resp.status_code}")
        if resp.headers.get("content-type", "").startswith("application/json"):
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return data
        else:
            print(resp.text)
            return {}
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return {}

def example_1():
    print("\n=== Example 1: Entity Correction ===")
    transcript = [
        {
            "end_timestamp": 49.5,
            "is_seller": False,
            "language": None,
            "speaker": "Anubhav Singh",
            "speaker_id": 100,
            "start_timestamp": 44,
            "text": "Hello. Hello. Thank you. Am I audible? Hi, Mohit."
        },
        {
            "end_timestamp": 69.5,
            "is_seller": True,
            "language": None,
            "speaker": "Rohit Agarwal",
            "speaker_id": 200,
            "start_timestamp": 50,
            "text": "Bank of America is in America."
        },
        {
            "end_timestamp": 73.5,
            "is_seller": False,
            "language": None,
            "speaker": "Anubhav Singh",
            "speaker_id": 100,
            "start_timestamp": 70,
            "text": "Pepsi is the organization we are working in. It is located in Bengu"
        }
    ]
    metadata = {
        "people": ["Rohit"],
        "companies": ["Pepsales"],
        "locations": ["Bengaluru"],
        "frameworks": ["BANT"]
    }
    call_run(transcript, metadata)

def example_2():
    print("\n=== Example 2: Grammar and Punctuation Enhancement ===")
    transcript = [
        {
            "end_timestamp": 120.5,
            "is_seller": False,
            "language": None,
            "speaker": "Client Name",
            "speaker_id": 300,
            "start_timestamp": 115,
            "text": "um so like our budget is around you know fifty thousand and we need this by next quarter i think"
        }
    ]
    metadata = {
        "people": ["Sarah"],
        "companies": ["TechCorp"],
        "locations": ["Mumbai"],
        "frameworks": ["MEDDIC"]
    }
    call_run(transcript, metadata)

def example_3():
    print("\n=== Example 3: Location and Company Correction ===")
    transcript = [
        {
            "end_timestamp": 95.5,
            "is_seller": False,
            "language": None,
            "speaker": "Prospect",
            "speaker_id": 500,
            "start_timestamp": 88,
            "text": "We at Micro Soft have offices in Bangalore and chen nai"
        }
    ]
    metadata = {
        "people": ["John"],
        "companies": ["Microsoft"],
        "locations": ["Bengaluru", "Chennai"],
        "frameworks": ["BANT"]
    }
    call_run(transcript, metadata)

def example_4():
    print("\n=== Example 4: Multiple Corrections Combined ===")
    transcript = [
        {
            "end_timestamp": 210.5,
            "is_seller": True,
            "language": None,
            "speaker": "Sales Person",
            "speaker_id": 600,
            "start_timestamp": 200,
            "text": "so um Dave from amazon web services based in hyd mentioned that they need SAAS solution by Q1"
        }
    ]
    metadata = {
        "people": ["David"],
        "companies": ["AWS"],
        "locations": ["Hyderabad"],
        "frameworks": ["MEDDIC"]
    }
    call_run(transcript, metadata)

def main():
    print(f"POST {URL}")
    example_1()
    example_2()
    example_3()
    example_4()

if __name__ == "__main__":
    main()
