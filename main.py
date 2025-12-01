"""
Main application for processing swim FIT files and generating reports.
"""
import argparse
import os
import sys
from pathlib import Path
from fit_parser import FITParser
from drive_uploader import DriveUploader
from report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Process swim FIT files and generate beautiful reports'
    )
    parser.add_argument(
        '--fit-file',
        type=str,
        action='append',
        help='Path to a FIT file to process (can be used multiple times)'
    )
    parser.add_argument(
        '--fit-files',
        type=str,
        nargs='+',
        help='Multiple FIT files to process (alternative to --fit-file)'
    )
    parser.add_argument(
        '--upload-to-drive',
        action='store_true',
        help='Upload FIT file to Google Drive'
    )
    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='Skip Google Drive upload (default behavior)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='reports',
        help='Directory to save generated reports (default: reports)'
    )
    parser.add_argument(
        '--drive-folder',
        type=str,
        default='Swim FIT Files',
        help='Google Drive folder name for uploads (default: Swim FIT Files)'
    )
    
    args = parser.parse_args()
    
    # Collect all FIT files
    fit_files = []
    if args.fit_files:
        fit_files.extend(args.fit_files)
    if args.fit_file:
        fit_files.extend(args.fit_file)
    
    if not fit_files:
        print("Error: No FIT files specified. Use --fit-file or --fit-files")
        sys.exit(1)
    
    # Validate all FIT files exist
    for fit_file in fit_files:
        if not os.path.exists(fit_file):
            print(f"Error: FIT file not found: {fit_file}")
            sys.exit(1)
    
    print("🏊 Swim FIT File Processor")
    print("=" * 50)
    
    # Step 1: Parse all FIT files
    print(f"\n[1/3] Parsing {len(fit_files)} FIT file(s)...")
    all_swim_data = []
    fit_filenames = []
    
    for i, fit_file in enumerate(fit_files, 1):
        print(f"\n   Parsing file {i}/{len(fit_files)}: {os.path.basename(fit_file)}")
        try:
            fit_parser = FITParser(fit_file)
            swim_data = fit_parser.parse()
            all_swim_data.append(swim_data)
            fit_filenames.append(os.path.basename(fit_file))
            
            # Display summary
            summary = swim_data.get('summary', {})
            print(f"   ✅ Distance: {summary.get('total_distance_m', 0):.0f}m")
            print(f"      Time: {summary.get('total_time', 'N/A')}")
            print(f"      Laps: {summary.get('num_laps', 0)}")
            print(f"      Strokes: {summary.get('total_strokes', 0)}")
            
        except Exception as e:
            print(f"   ❌ Error parsing FIT file: {str(e)}")
            sys.exit(1)
    
    # Step 2: Upload to Google Drive (if requested)
    drive_links = []
    if args.upload_to_drive and not args.no_upload:
        print(f"\n[2/3] Uploading {len(fit_files)} file(s) to Google Drive...")
        try:
            uploader = DriveUploader()
            uploader.authenticate()
            for fit_file in fit_files:
                file_id, web_link, folder_id = uploader.upload_fit_file(
                    fit_file,
                    args.drive_folder
                )
                drive_links.append(web_link)
                print(f"   ✅ Uploaded: {os.path.basename(fit_file)}")
        except FileNotFoundError as e:
            print(f"⚠️  Warning: {str(e)}")
            print("   Skipping Google Drive upload. Run with --no-upload to suppress this warning.")
        except Exception as e:
            print(f"❌ Error uploading to Google Drive: {str(e)}")
            print("   Continuing with report generation...")
    else:
        print(f"\n[2/3] Skipping Google Drive upload")
    
    # Step 3: Generate report
    print(f"\n[3/3] Generating swim report with {len(all_swim_data)} workout(s)...")
    try:
        report_gen = ReportGenerator(all_swim_data, args.output_dir)
        result = report_gen.generate_multi_workout_report(fit_filenames)
        
        # Handle both single and multi-workout reports
        if isinstance(result, tuple):
            report_path, pdf_path = result
        else:
            report_path = result
            pdf_path = None
        
        print(f"✅ Report generated successfully!")
        print(f"   HTML report: {report_path}")
        print(f"   Open in browser: file://{os.path.abspath(report_path)}")
        
        if pdf_path:
            print(f"   PDF report: {pdf_path}")
        else:
            print(f"   PDF generation skipped (install weasyprint for PDF support)")
        
        if drive_links:
            print(f"\n📊 Summary:")
            for i, link in enumerate(drive_links, 1):
                print(f"   Workout {i} uploaded to: {link}")
            print(f"   Report generated: {report_path}")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✨ Processing complete!")


if __name__ == '__main__':
    main()

