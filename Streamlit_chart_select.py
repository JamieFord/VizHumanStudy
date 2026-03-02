import streamlit as st
from PIL import Image
import sqlite3
import os

# Specify the directory path
#directory = '/home/james/Text2Vis/Images/gpt5-nano-Polishing_Sample'  #### On Linux
directory = 'gpt5-nano-Polishing_Sample' ### For GitHub

# Get a sorted list of files in the directory
sorted_files = sorted(os.listdir(directory))

def create_table():
    conn = sqlite3.connect('responses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS responses
                 (userID TEXT, comparison_num INTEGER, image_num TEXT, rating1 TEXT, rating2 TEXT, rating3 TEXT,
                    rating4 TEXT, rating5 TEXT, rating6 TEXT, rating7 TEXT, rating8 TEXT, rating9 TEXT, rating10 TEXT, 
                    rating11 TEXT, rating12 TEXT, rating13 TEXT, rating14 TEXT, rating15 TEXT, rating16 TEXT, rating17 TEXT)''')
    conn.commit()
    conn.close()

def save_response(userid, comparison_num, image_num, **ratings):
    conn = sqlite3.connect('responses.db')
    c = conn.cursor()
    
    # Common fixed columns: userid, comparison_num, image_num + ratings 1-17
    base_columns = ['userid', 'comparison_num', 'image_num']
    rating_columns = [f'rating{i}' for i in range(1, 18)]
    all_columns = base_columns + rating_columns
    
    # Build values list (empty string for missing ratings)
    values = [userid, comparison_num, image_num]
    for i in range(1, 18):
        values.append(ratings.get(f'Rating{i}', ''))
    
    # Dynamic placeholders and column list for SQL
    placeholders = ','.join(['?' for _ in values])
    columns_str = ','.join(all_columns)
    
    query = f"INSERT INTO responses ({columns_str}) VALUES ({placeholders})"
    
    c.execute(query, values)
    conn.commit()
    conn.close()


def max_completions(userID):
    # Connect to the SQLite database
    conn = sqlite3.connect('responses.db')
    cursor = conn.cursor()
    # SQL query to get the max comparison_num for the specific userID
    query = """
    SELECT IFNULL(MAX(comparison_num), 0) as max_comparison_num
    FROM responses
    WHERE userID = ?
    """
    # Execute the query with the userID parameter
    cursor.execute(query, (userID,))
    # Fetch the result
    result = cursor.fetchone()
    # Close the connection
    conn.close()
    return result[0] if result and result[0] is not None else 0

create_table()

if 'stage' not in st.session_state:
    st.session_state.stage = 'user_id'
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

def image_comparison(comparison_num, image_a):
    st.header(f"Image Comparison {comparison_num}")
    max_complete = max_completions(st.session_state.user_id)
    st.write("")
    st.write(f"User {st.session_state.user_id}, you have completed {max_complete} comparison(s).")
    st.write("")
    
    image_a_path = image_a
    image_a_img = Image.open(image_a_path)
    st.image(image_a_img, caption=f'Rate Chart {image_a} on the following items:', width="stretch")

    # Extract chart type from filename
    chart_name = os.path.basename(image_a_path)  # Gets "bar_something.png"
    chart_type = chart_name.split('_', 1)[0] if '_' in chart_name else "unknown"

    # Determine key using your exact match logic
    key = chart_type
    match chart_type:
        case "bar" | "barh" | "bar (horizontal)" | "horizontal bar chart" | "grouped bar chart":
            key = "bar"
        case "box" | "boxplot" | "violin":
            key = "box"
        case "combined" | "combined line and bar chart" | "line and bar" | "pareto chart (bar chart with cumulative line)" | "line and scatter":
            key = "combined"
        case "dot" | "dot plot":
            key = "dot"
        case "line" | "line " | "line chart with dual y-axes" | "line with dual y-axes" | "area" | "grouping line":
            key = "line"
        case "pie" | "donut":
            key = "pie"
        case "scatter" | "grouping scatter":
            key = "scatter"
        case "stacked" | "stacked area" | "stacked bar":
            key = "stacked"
        case _:
            pass

    # YOUR COMPLETE criteria dictionary with ALL type-specific questions
    criteria = {
        "bar": [
            {"id": "10", "name": "Inappropriate Use of Bar Chart", "check": "bar charts appropriate for the data type"},
            {"id": "11", "name": "Inconsistent Bar Widths", "check": "bars are not of the same width"},
            {"id": "12", "name": "Inappropriate Axis Range", "check": "the selected range for axes compresses or stretches the visual impact of variations"},
            {"id": "13", "name": "Truncated Axis", "check": "the axis starts at non-zero, unless the data context justifies a non-zero starting point"},
            {"id": "14", "name": "Overuse of Gridlines", "check": "the gridlines uses too many or inconsistent gridlines"},
            {"id": "15", "name": "Dual Axis", "check": "the chart has dual y-axes, unless the two y-axes have the same scale"},
            {"id": "16", "name": "Missing Axis Title", "check": "the meaning of the axis and units of measurement is unclear when the chart does not have implicit or explicit axis titles"},
            {"id": "17", "name": "Inconsistent Tick Intervals", "check": "any tick marks on the axes are unevenly spaced"}
        ],
        "line": [
            {"id": "10", "name": "Inappropriate Use of Area/Line Chart", "check": "chart depicts continuous data and with correct axis orientation"},
            {"id": "11", "name": "Inappropriate Axis Range", "check": "the selected range for axes compresses or stretches the visual impact of variations"},
            {"id": "12", "name": "Truncated Axis", "check": "the axis starts at non-zero, unless the data context justifies a non-zero starting point"},
            {"id": "13", "name": "Overuse of Gridlines", "check": "the gridlines uses too many or inconsistent gridlines"},
            {"id": "14", "name": "Dual Axis", "check": "the chart has dual y-axes, unless the two y-axes have the same scale"},
            {"id": "15", "name": "Missing Axis Title", "check": "the meaning of the axis and units of measurement is unclear when the chart does not have implicit or explicit axis titles"},
            {"id": "16", "name": "Inconsistent Tick Intervals", "check": "any tick marks on the axes are unevenly spaced"}
        ],
        "pie": [
            {"id": "10", "name": "Inappropriate Use of Pie Chart", "check": "chart depicts part-to-whole relationships with a small number of categories, typically no more than 5-7 slices"},
            {"id": "11", "name": "Label Clarity", "check": "labels or percentages fit clearly without excessive leader lines or overlap"},
            {"id": "12", "name": "Excessive Thin Slices", "check": "any slice is under 5 percent or too narrow to distinguish reliably from adjacent areas"},
            {"id": "13", "name": "Color Differentiation Failure", "check": "adjacent slices have sufficient contrast; avoid similar shades that blend together"}
        ],
        "scatter": [
            {"id": "10", "name": "Inappropriate Use of Scatterplot", "check": "chart depicts relationships between two variables"},
            {"id": "11", "name": "Points Displayed", "check": "the sample size is appropriate; too few points may not show a pattern, too many points may cause overplotting"},
            {"id": "12", "name": "Axis Scaling Issues", "check": "both axes use appropriate scales (linear/log) that honestly represent data relationships without artificial compression"},
            {"id": "13", "name": "Truncated or Zero-Breaking Axes", "check": "axes start at zero or use broken scales only when justified, avoiding distortion of slopes or clusters"}
        ],
        "box": [
            {"id": "10", "name": "Inappropriate Use of Boxplot", "check": "the data is continuous and numeric rather than categorical counts"},
            {"id": "11", "name": "Number of Categories", "check": " the number of categories is small enough to compare boxes without overcrowding"}
        ],
        "histogram": [
            {"id": "10", "name": "Inappropriate Use of Histogram", "check": "the chart depicts the distribution of a single continuous variable, not comparisons of many series"},
            {"id": "11", "name": "Binning", "check": "binning is meaningful (consistent bin widths, appropriate bin count) and not hiding important structure"},
            {"id": "12", "name": "Bars Not Touching", "check": "adjacent bars touch to properly indicate continuous data ranges, with gaps only for empty bins"},
            {"id": "13", "name": "Non-Zero Y-Axis Baseline", "check": "the y-axis starts at zero to accurately represent frequency or density heights without distortion"}
        ],
        "candlestick": [
            {"id": "10", "name": "Inappropriate Use of Candlestick Chart", "check": "the underlying data includes open, high, low, and close values for each time period"},
            {"id": "11", "name": "Inconsistent Time Axis Scaling", "check": "x-axis uses linear time intervals without gaps or irregular spacing that misrepresents periods"},
            {"id": "12", "name": "Unclear Zero Line Reference", "check": "a subtle horizontal line at the initial price provides baseline for gains/losses without clutter"}
        ],
        "funnel": [
            {"id": "10", "name": "Inappropriate Use of Funnel Chart", "check": "the process is sequential, with ordered stages; avoid funnels for unordered categories"},
            {"id": "11", "name": "Related Stages", "check": "each stage represents a subset or progression of the previous stage, not unrelated metrics"},
            {"id": "12", "name": "Number of Stages", "check": "there are a reasonable number of stages (typically 3â€“7) so the funnel remains readable"},
            {"id": "13", "name": "Poor Color Differentiation", "check": "sequential colors create clear stage separation without blending adjacent sections"}
        ],
        "treemap": [
            {"id": "10", "name": "Inappropriate Use of Treemap", "check": "the goal is to show a part-to-whole hierarchy; avoid treemaps for non-hierarchical data"},
            {"id": "11", "name": "Label Placement Issues", "check": "text fits large rectangles legibly (high contrast) and avoids cluttering small ones"}
        ],
        "subplot": [
            {"id": "10", "name": "Overall Title Clarity", "check": "main figure title explains all subplots"},
            {"id": "11", "name": "Consistent Color Schemes", "check": "all subplots use matching color palettes"},
            {"id": "12", "name": "Shared Axis Alignment", "check": "shared axes have consistent labeling/scaling"}
        ],
        "waterfall": [
            {"id": "10", "name": "Inappropriate Use of Waterfall Chart", "check": "components are truly additive (or subtractive) and logically ordered"},
            {"id": "11", "name": "Axis Scaling Distortion", "check": "y-axis starts at zero (or justified break) to preserve true proportional impact of changes"}
        ],
        "bubble": [
            {"id": "10", "name": "Inappropriate Use of Bubble Chart", "check": "chart is appropriate for showing three variables (x, y, and a third encoded by size)chart is showing three variables (x, y, and a third encoded by size)"},
            {"id": "11", "name": "Ambiguous Bubble Size Meaning", "check": "it is clear what the bubble size represents (e.g., population, revenue, count)"},
            {"id": "12", "name": "Too Many Bubbles", "check": "there are so many bubbles that patterns are hard to see and individual points are indistinguishable or overlap"},
            {"id": "13", "name": "Misleading Axes Scales", "check": "axis scales (linear vs log, min/max) are appropriate for the data and do not distort relationships"}
        ],
        "choropleth": [
            {"id": "10", "name": "Poor Color Scheme Choice", "check": "sequential/diverging color palettes are intuitive, colorblind-friendly, and show clear lightness steps from low to high values"},
            {"id": "11", "name": "Too Many Color Classes", "check": "3-7 classes max are used; more than 7 shades obscure differences and overwhelm readers"},
            {"id": "12", "name": "Distracting Borders/Outlines", "check": "heavy strokes or borders overpower fills; use thin/soft/none for focus on colors"},
            {"id": "13", "name": "Overplotting Labels", "check": "region labels are sparse, legible, and non-overlapping"},
            {"id": "14", "name": "Excessive Map Elements", "check": "unnecessary gridlines, backgrounds, or annotations clutter the geographic patterns"}
        ],
        "heatmap": [
            {"id": "10", "name": "Unordered Rows/Columns", "check": "rows and columns are clustered, sorted logically (e.g., by total), or hierarchical to reveal patterns"},
            {"id": "11", "name": "Poor Color Scale Choice", "check": "sequential (low-to-high) or diverging palettes match data type, with clear lightness progression and colorblind accessibility"},
            {"id": "12", "name": "Tiny Cell Sizes", "check": "cells are large enough to distinguish color differences"},
            {"id": "13", "name": "Unhandled Missing Values", "check": "missing data is explicitly marked, imputed, or excluded rather than distorting color patterns"}
        ],
        "radar": [
            {"id": "10", "name": "Inappropriate Use of Radar Chart", "check": "chart suits 3-8 cyclical or profile variables"},
            {"id": "11", "name": "Inconsistent Axis Scales", "check": "all axes use the same scale range (starting at zero) or normalized data to prevent distortion"},
            {"id": "12", "name": "Crowded or Unclear Labels", "check": "axis labels are concise, consistently placed, and legible without rotation clutter"},
            {"id": "13", "name": "Missing Gridlines", "check": "radial and circular gridlines aid value estimation without excessive visual noise"}
        ],
        "combined": [
            {"id": "10", "name": "Dual Axis Scale Mismatch", "check": "secondary y-axis scales are compatible and clearly labeled to avoid trend distortion"},
            {"id": "11", "name": "Legend Overload Confusion", "check": "bar/line/point meanings are instantly clear without repeated legend reference"},
            {"id": "12", "name": "Unrelated or Too Many Data Series", "check": "series share logical relationship and common category axis, or if there are too many series for clear interpretation"}
        ],
        "dot": [
            {"id": "10", "name": "Inconsistent Dot Size", "check": "all dots maintain fixed uniform size"},
            {"id": "11", "name": "Misaligned Dot Positioning", "check": "dots precisely align to the value axis scale for accurate position-based reading"}
        ],
        "stacked": [
            {"id": "10", "name": "Inappropriate Use of Stacked Charts", "check": "chart stacks too many layers"},
            {"id": "11", "name": "Inappropriate Axis Range", "check": "the selected range for axes compresses or stretches the visual impact of variations"},
            {"id": "12", "name": "Truncated Axis", "check": "the axis starts at non-zero, unless the data context justifies a non-zero starting point"},
            {"id": "13", "name": "Overuse of Gridlines", "check": "the gridlines uses too many or inconsistent gridlines"},
            {"id": "14", "name": "Dual Axis", "check": "the chart has dual y-axes, unless the two y-axes have the same scale"},
            {"id": "15", "name": "Missing Axis Title", "check": "the meaning of the axis and units of measurement is unclear when the chart does not have implicit or explicit axis titles"},
            {"id": "16", "name": "Inconsistent Tick Intervals", "check": "any tick marks on the axes are unevenly spaced"}
        ]
    }

    # 9 COMMON questions (always shown)
    common_questions = [
        "Overusing Colors: Check if colors are used judiciously and meaningfully",
        "Missing Value Labels: Check if data points within the chart are labeled with their respective values when axes or legends do not provide sufficient details",
        "Overplotting: Check if unintentional overlaps obscure patterns",
        "Color Blind Unfriendly: Check if there is information loss when people with Deuteranopia, Protanopia, or Tritanopia color blindness see the chart image",
        "Cluttering: Check if density makes patterns unrecognizable for this chart type",
        "Missing Title: Check if there is a clear, descriptive title",
        "Missing Units: Check if the units of measurement are indicated",
        "Data of Different Magnitudes: Check if two series with vastly different magnitudes are on the same scale",
        "3D: Check if there is unnecessary 3D for 2D data, reserving 3D for inherently three-dimensional data or complex spatial relationships"
    ]

    # Get type-specific questions and combine
    type_questions = [f"{crit['name']}: Check if {crit['check']}" for crit in criteria.get(key, [])]
    all_questions = common_questions + type_questions

    # Dynamic radio buttons
    ratings = {}
    for i, question in enumerate(all_questions, 1):
        ratings[f"Rating{i}"] = st.radio(
            question, 
            ('Passes', 'Problem'), 
            index=None,  # No default selection, 
            horizontal=True, 
            key=f"rating_{comparison_num}_{i}"
        )

    if st.button('Submit'):
        image_num = os.path.basename(image_a_path)
        rating_vars = {f"Rating{i}": ratings.get(f"Rating{i}", '') for i in range(1, 18)}
        save_response(st.session_state.user_id, comparison_num, image_num, **rating_vars)
        st.write(f"Your response has been saved.")
        st.session_state.current_comparison += 1
        st.rerun()


# Initialize session state
if 'stage' not in st.session_state:
    st.session_state.stage = 'user_id'
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_comparison' not in st.session_state:
    st.session_state.current_comparison = None

# Directory paths
#directory = '/home/james/Text2Vis/Images/gpt4o-mini_Baseline'  # Replace with your directory path
#ReWriter_dir = '/home/james/Text2Vis/Images/gpt4o-mini_Agent_Rewriter'
#Polished_dir = '/home/james/Text2Vis/Images/gpt5-nano-Polishing'

# Get sorted list of files
total_files = len(sorted_files)

if st.session_state.stage == 'user_id':
    st.header("Select User ID")
    user_id = st.radio("Choose your User ID:", ('Sashank', 'Veronica', 'Dr. Rios','James'))
    if st.button('Continue'):
        st.session_state.user_id = user_id
        max_complete = max_completions(st.session_state.user_id)
        st.session_state.current_comparison = max_complete + 1
        st.session_state.stage = 'comparison'
        st.rerun()

elif st.session_state.stage == 'comparison':
    if st.session_state.current_comparison <= total_files:
        file_index = st.session_state.current_comparison - 1
        filename = sorted_files[file_index]
        original_path = os.path.join(directory, filename)
        #ReWriter_path = os.path.join(ReWriter_dir, f'{filename}')
        #Polished_path = os.path.join(Polished_dir, f'{filename}')
        
        image_comparison(st.session_state.current_comparison, original_path)
    else:
        st.session_state.stage = 'thank_you'
        st.rerun()

elif st.session_state.stage == 'thank_you':
    st.header("Thank you!")
    st.write(f"User {st.session_state.user_id}, you have completed all ratings.")
    if st.button('Start Over'):
        st.session_state.stage = 'thank_you'
        st.session_state.user_id = None
        st.session_state.current_comparison = None
        st.rerun()