# HTML Travel Comparison Generator

This MCP tool allows you to generate beautiful, professional HTML travel comparison reports for commute planning.

## MCP Function: `generate_travel_comparison_html`

### Purpose
Creates styled HTML reports comparing different travel options (ferry vs driving) with cost breakdowns, schedules, and recommendations.

### Usage

```python
# Example usage through the MCP server
result = generate_travel_comparison_html(
    event_name="Seattle AI & ML Meetup",
    event_date="Monday, August 5th, 2025", 
    event_time="6:00 PM - 8:00 PM",
    event_location="Seattle Central Library, 1000 4th Ave, Seattle, WA",
    origin_address="Fireweed & Sydney, Port Orchard",
    travel_options=[
        {
            "name": "Ferry via Southworth",
            "route_details": [
                "Drive to Southworth Terminal (6.8 mi)",
                "30-40 min ferry to Fauntleroy",
                "21 min drive to venue"
            ],
            "travel_time": "~1 hour 15 min",
            "distance": "13.6 miles driving + ferry crossing",
            "cost": "$48 - $58",
            "pros_cons": [
                "✅ Most cost-effective",
                "✅ Shorter ferry ride",
                "❌ Requires ferry timing"
            ],
            "recommended": True
        },
        {
            "name": "Drive Around",
            "route_details": [
                "Drive via I-5 around Puget Sound",
                "Direct route to downtown Seattle"
            ],
            "travel_time": "1 hour 4 min",
            "distance": "~110 miles total",
            "cost": "$100 - $110", 
            "pros_cons": [
                "✅ Flexible timing",
                "❌ Most expensive",
                "❌ Traffic stress"
            ],
            "recommended": False
        }
    ],
    recommended_option="Southworth Ferry Option",
    cost_breakdown={
        "Southworth-Fauntleroy": {
            "ferry_fare": "$27.80",
            "mileage": "$10.47",
            "parking": "$10 - $20",
            "total": "$48.27 - $58.27"
        },
        "Drive Around": {
            "ferry_fare": "$0.00", 
            "mileage": "$84.70",
            "parking": "$15 - $25",
            "total": "$99.70 - $109.70"
        }
    },
    pro_tips=[
        "• Ferry option saves $42-62 compared to driving",
        "• Check for direct ferry routes to save 10 minutes",
        "• Arrive at ferry terminal 15 minutes early"
    ]
)
```

### Return Value

```python
{
    "html_content": "<html>...</html>",  # Complete HTML string
    "filename": "travel_comparison_Seattle_AI_ML_Meetup_20250730_140000.html",
    "template_used": "/path/to/template.html",
    "status": "success"
}
```

## Features

### 🎨 **Beautiful Styling**
- Modern gradient backgrounds
- Responsive design for mobile/desktop
- Professional typography and spacing
- Hover effects and smooth transitions

### 📊 **Comprehensive Comparison**
- Side-by-side travel options
- Cost breakdowns with detailed components
- Time/distance analysis
- Pros and cons for each option

### 📅 **Detailed Scheduling**
- Step-by-step itinerary
- Alternative ferry times
- Highlighted key departure times
- Buffer time recommendations

### 💡 **Smart Recommendations**
- Automatically highlights the best option
- Calculates savings between options
- Provides contextual pro tips
- Emphasizes cost-effective choices

## Template Structure

The HTML template (`data/travel_comparison_template.html`) uses these variables:

### Required Variables
- `{{event_name}}` - Event title
- `{{event_date}}` - Event date
- `{{event_time}}` - Event time range
- `{{event_location}}` - Venue address
- `{{origin_address}}` - Starting location
- `{{travel_options}}` - Generated table rows for options

### Optional Sections
- `{{savings_message}}` - Savings highlighting
- `{{cost_breakdown_section}}` - Detailed cost table
- `{{recommended_schedule_section}}` - Step-by-step schedule
- `{{alternative_times_section}}` - Alternative ferry times
- `{{pro_tips}}` - List of helpful tips

## Integration with Other MCP Tools

This function works perfectly with your other MCP tools:

1. **Use `find_nearby_ferry_terminals`** to get terminal options
2. **Use `ferry_cost`** to get accurate pricing data
3. **Use `drive_time_tool`** to calculate drive times
4. **Use `get_ferry_times`** to get schedule information
5. **Generate the beautiful HTML report** with all the data

## Example Workflow

```python
# 1. Find ferry terminals near origin
terminals = find_nearby_ferry_terminals("Port Orchard, WA", max_results=2)

# 2. Get ferry costs for each terminal 
southworth_cost = ferry_cost("2025-08-05", 4, 7, round_trip=True)
bremerton_cost = ferry_cost("2025-08-05", 1, 3, round_trip=True)

# 3. Get drive times
drive_to_southworth = drive_time_tool("Port Orchard, WA", "Southworth Ferry Terminal")
drive_direct = drive_time_tool("Port Orchard, WA", "Seattle Central Library")

# 4. Compile travel options and generate HTML report
html_report = generate_travel_comparison_html(
    # ... compile all the data from above steps
)

# 5. Save or display the beautiful HTML report
```

This creates a professional, comprehensive travel comparison that helps users make informed commuting decisions!
