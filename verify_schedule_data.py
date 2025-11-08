#!/usr/bin/env python3
"""
Verify and analyze ferry schedule data

This script checks the current static ferry schedule file and provides
statistics and validation.
"""

import json
from pathlib import Path
from datetime import datetime


def analyze_schedule(schedule_file: Path):
    """Analyze the ferry schedule file"""

    print("=" * 70)
    print("Ferry Schedule Analysis")
    print("=" * 70)

    if not schedule_file.exists():
        print(f"\n✗ Schedule file not found: {schedule_file}")
        return

    # Load the schedule
    with open(schedule_file, 'r') as f:
        schedules = json.load(f)

    print(f"\nSchedule file: {schedule_file.name}")
    print(f"Total routes: {len(schedules)}")

    print("\n" + "-" * 70)
    print("Route Details:")
    print("-" * 70)

    for route_key, route_data in schedules.items():
        directions = route_data.get('direction', [])
        weekday_sailings = route_data.get('weekday', [])
        weekend_sailings = route_data.get('weekend', [])

        print(f"\n{route_key.upper()}")
        print(f"  Directions: {', '.join(directions)}")
        print(f"  Weekday sailings: {len(weekday_sailings)}")
        print(f"  Weekend sailings: {len(weekend_sailings)}")

        # Show first and last sailing times
        if weekday_sailings:
            first = weekday_sailings[0].get('time', 'N/A')
            last = weekday_sailings[-1].get('time', 'N/A')
            crossing = weekday_sailings[0].get('crossing_time', 'N/A')
            print(f"  Weekday: {first} - {last} (crossing: {crossing} min)")

        if weekend_sailings:
            first = weekend_sailings[0].get('time', 'N/A')
            last = weekend_sailings[-1].get('time', 'N/A')
            crossing = weekend_sailings[0].get('crossing_time', 'N/A')
            print(f"  Weekend: {first} - {last} (crossing: {crossing} min)")

        # Check for annotations
        weekday_annotations = sum(1 for s in weekday_sailings if s.get('annotations'))
        weekend_annotations = sum(1 for s in weekend_sailings if s.get('annotations'))

        if weekday_annotations or weekend_annotations:
            print(f"  Sailings with annotations: {weekday_annotations} weekday, {weekend_annotations} weekend")

    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)

    total_weekday = sum(len(r.get('weekday', [])) for r in schedules.values())
    total_weekend = sum(len(r.get('weekend', [])) for r in schedules.values())

    print(f"Total weekday sailings: {total_weekday}")
    print(f"Total weekend sailings: {total_weekend}")
    print(f"Total sailings: {total_weekday + total_weekend}")

    # Check for data consistency
    print("\n" + "=" * 70)
    print("Data Validation:")
    print("=" * 70)

    issues = []

    for route_key, route_data in schedules.items():
        # Check for required fields
        if not route_data.get('direction'):
            issues.append(f"{route_key}: Missing direction information")

        if not route_data.get('weekday'):
            issues.append(f"{route_key}: No weekday sailings")

        if not route_data.get('weekend'):
            issues.append(f"{route_key}: No weekend sailings")

        # Check sailing data
        for day_type in ['weekday', 'weekend']:
            sailings = route_data.get(day_type, [])
            for idx, sailing in enumerate(sailings):
                if not sailing.get('time'):
                    issues.append(f"{route_key} ({day_type} #{idx+1}): Missing time")

                if 'crossing_time' not in sailing:
                    issues.append(f"{route_key} ({day_type} #{idx+1}): Missing crossing_time")

    if issues:
        print(f"\n⚠ Found {len(issues)} issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  • {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")
    else:
        print("\n✓ No issues found - schedule data looks good!")

    print("\n" + "=" * 70)


def main():
    """Main entry point"""
    schedule_file = Path(__file__).parent / 'data' / 'static_ferry_schedules.json'
    analyze_schedule(schedule_file)


if __name__ == '__main__':
    main()
