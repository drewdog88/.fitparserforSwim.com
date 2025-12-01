# Garmin FIT Swim Report Generator

A comprehensive Python application to process swim.com FIT files, upload them to Google Drive, and generate beautiful, detailed visual reports for each swim session.

## 🏊 Features

- **FIT File Parsing**: Extracts comprehensive swim data from Garmin FIT files
  - Session metrics (distance, time, pace, strokes)
  - Lap-by-lap analysis
  - Length-by-length details
  - Active swim time vs. rest time
  - Stroke type detection (freestyle, backstroke, breaststroke, butterfly, drill)
  - Pool length detection (meters/yards)

- **Google Drive Integration**: Automatically upload FIT files to Google Drive
  - OAuth 2.0 authentication
  - Organized folder structure
  - Direct file links

- **Beautiful Visual Reports**: Generate professional HTML and PDF reports
  - **Multi-workout support**: Tabbed interface for multiple workouts + cumulative view
  - **Interactive charts**: Pace, distance, heart rate, lap analysis
  - **Stroke visualization**: Custom icons for each stroke type
  - **Time formatting**: Readable H:MM:SS format for total time, MM:SS for pace values
  - **Unit conversion**: Automatic detection and display of meters/yards
  - **Comprehensive metrics**: Active time, rest time, average pace (calculated from lap paces), average strokes per lap
  - **Export to PDF**: Share-ready PDF reports

## 📋 Requirements

- Python 3.8 or higher
- Google Cloud Project with Drive API enabled (for Drive upload feature)
- Playwright (for PDF generation)

## 🚀 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/drewdog88/.fitparserforSwim.com.git
cd .fitparserforSwim.com
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers (for PDF generation):**
```bash
playwright install chromium
```

4. **Set up Google Drive API (optional, for upload feature):**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Drive API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials as `credentials.json` and place in project root
   - The first time you run with `--upload-to-drive`, you'll be prompted to authenticate

## 📖 Usage

### Basic Usage - Single Workout

Process a single FIT file and generate a report:

```bash
python main.py --fit-file path/to/your/file.fit --no-upload
```

### Multiple Workouts

Process multiple FIT files and generate a tabbed report:

```bash
python main.py --fit-files workout1.fit workout2.fit workout3.fit --no-upload
```

Or using the alternative syntax:

```bash
python main.py --fit-file workout1.fit --fit-file workout2.fit --no-upload
```

### With Google Drive Upload

Upload FIT files to Google Drive and generate reports:

```bash
python main.py --fit-files workout1.fit workout2.fit --upload-to-drive
```

### Generate PDF Report

PDF generation is automatic when processing files. The PDF will be saved alongside the HTML report.

### Command Line Options

```
--fit-file PATH          Path to a FIT file (can be used multiple times)
--fit-files PATH ...     Multiple FIT files to process
--upload-to-drive        Upload FIT files to Google Drive
--no-upload             Skip Google Drive upload (default)
--output-dir DIR         Directory to save reports (default: reports)
--drive-folder NAME      Google Drive folder name (default: "Swim FIT Files")
```

## 📁 Project Structure

```
.fitparserforSwim.com/
├── main.py                      # Main application entry point
├── fit_parser.py                # FIT file parsing module
├── drive_uploader.py            # Google Drive integration
├── report_generator.py          # Report generation with visualizations
├── utils.py                     # Utility functions (stroke icons, formatting)
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
│
├── templates/                   # HTML report templates
│   ├── swim_report.html         # Single workout template
│   └── swim_report_multi.html   # Multi-workout template with tabs
│
├── icons/                       # Stroke type icons
│   └── strokes/
│       ├── freestyle.png
│       ├── backstroke.png
│       ├── breaststroke.png
│       ├── butterfly.png
│       └── drill.png
│
└── reports/                     # Generated reports (gitignored)
    ├── icons/                   # Copied icons for reports
    ├── *.html                   # HTML reports
    └── *.pdf                    # PDF reports
```

## 🔧 How It Works

### 1. FIT File Parsing (`fit_parser.py`)

The parser extracts data from FIT files using the `fitdecode` library:

- **Session Data**: Overall workout summary
  - Total distance, time, strokes
  - Average pace and speed
  - Pool length and type (meters/yards)
  - Active swim time vs. rest time
  - Number of active lengths

- **Lap Data**: Individual lap metrics
  - Lap time, distance, strokes
  - Stroke type per lap
  - Pace per lap

- **Length Data**: Individual pool length details
  - Length time and distance
  - Stroke count
  - Active vs. idle (rest) lengths

- **Record Data**: Detailed track points
  - Timestamp, distance, speed
  - Heart rate (if available)
  - GPS coordinates (if available)

### 2. Data Processing

The parser calculates:
- **Average pace**: 
  - Primary method: Averages individual lap paces from FIT file (matches swim.com app)
  - Fallback: Calculates from total distance divided by active swim time
  - Uses active swim time, not total elapsed time
- **Active swim time**: Sum of all active length times (swimming time only)
- **Rest time**: Sum of all idle length times (rest periods)
- **Average strokes per lap**: Calculated from total strokes divided by number of laps
- **Pool type detection**: Identifies yard pools based on pool length (25yd = 22.86m)
- **Unit conversion**: Converts between meters and yards as needed
- **Lap pace**: Calculated from lap distance and time if not provided in FIT file

### 3. Report Generation (`report_generator.py`)

Generates interactive HTML reports with:

- **Summary Cards**: Key metrics at a glance
- **Charts and Graphs**:
  - Pace over time (with MM:SS formatting)
  - Cumulative distance
  - Heart rate (if available)
  - Lap analysis
  - Lap-by-lap pace comparison
- **Stroke Breakdown**: Visual representation of stroke types
- **Multi-workout Support**: Tabbed interface for comparing workouts

### 4. PDF Export

Uses Playwright to convert HTML reports to PDF with:
- Full styling preservation
- All charts and images included
- Print-ready formatting

## 📊 Report Features

### Metrics Displayed

- **Distance**: Total swim distance (meters/yards)
- **Time**: Total elapsed time (H:MM:SS format), active swim time, rest time
- **Pace**: Average pace per 100m/100yd (calculated from lap paces when available, matching swim.com app)
- **Laps**: Number of active lengths
- **Avg Strokes per Lap**: Average stroke count per lap (more useful than total strokes)
- **Stroke Types**: Breakdown by stroke (freestyle, backstroke, etc.)

### Charts Included

1. **Pace Chart**: Pace per 100m/100yd over time
2. **Distance Chart**: Cumulative distance progression
3. **Heart Rate Chart**: Heart rate over time (if available)
4. **Lap Analysis**: Distance and time per lap
5. **Lap Pace Chart**: Pace comparison across laps

All charts include:
- Clear axis labels
- MM:SS time formatting
- Appropriate units (meters/yards)
- Interactive tooltips

## 🎨 Customization

### Stroke Icons

Replace icons in `icons/strokes/` directory:
- `freestyle.png`
- `backstroke.png`
- `breaststroke.png`
- `butterfly.png`
- `drill.png`

Icons are automatically copied to reports during generation.

### Report Templates

Modify templates in `templates/` directory:
- `swim_report.html`: Single workout template
- `swim_report_multi.html`: Multi-workout template

Templates use Jinja2 syntax for dynamic content.

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'fitdecode'"
```bash
pip install -r requirements.txt
```

### "WeasyPrint could not import some external libraries"
WeasyPrint has been replaced with Playwright. Install Playwright:
```bash
playwright install chromium
```

### "FileNotFoundError: credentials.json"
This is only needed for Google Drive upload. Either:
- Set up Google Drive API credentials (see Installation section)
- Use `--no-upload` flag to skip upload

### Pace calculation seems incorrect
The parser calculates average pace using multiple methods (in order of preference):
1. **Lap-level pace averaging**: Averages individual lap paces from the FIT file (matches swim.com app)
2. **Distance/active time calculation**: Calculates from total distance divided by active swim time
3. **Session avg_speed**: Uses session-level average speed if available

The pace uses **active swim time**, not total elapsed time, which matches swim.com app behavior. Verify:
- Active swim time is correctly extracted from length records
- Pool length is correctly detected (meters vs. yards)
- Distance units match pace units
- Lap-level pace data is available in the FIT file

## 📝 Data Privacy

- **FIT files are excluded from git** (see `.gitignore`)
- Personal swim data is never committed to the repository
- Google Drive credentials are excluded from git
- Generated reports are excluded from git

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available for personal use.

## 🙏 Acknowledgments

- Uses [fitdecode](https://github.com/polyvertex/fitdecode) for FIT file parsing
- Uses [Plotly](https://plotly.com/python/) for interactive charts
- Uses [Playwright](https://playwright.dev/python/) for PDF generation
- Stroke icons are custom graphics

## 📧 Support

For issues or questions, please open an issue on GitHub.

---

**Note**: This application is designed specifically for swim.com FIT files. While it may work with other Garmin FIT files, it's optimized for swim data structure.
