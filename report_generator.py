"""
Generate beautiful HTML reports with visualizations for swim data.
"""
import os
from datetime import datetime
from typing import Dict, List
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from jinja2 import Template
from utils import get_stroke_icon, get_stroke_name, get_stroke_icon_html, get_stroke_icon_path
import shutil


class ReportGenerator:
    """Generate beautiful HTML reports with swim data visualizations."""
    
    def __init__(self, swim_data, output_dir: str = 'reports'):
        # Accept either single dict or list of dicts
        if isinstance(swim_data, list):
            self.swim_data = swim_data[0] if len(swim_data) == 1 else None
            self.all_swim_data = swim_data
        else:
            self.swim_data = swim_data
            self.all_swim_data = [swim_data]
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Create icons directory in reports folder and copy icons
        self.icons_dir = os.path.join(output_dir, 'icons')
        os.makedirs(self.icons_dir, exist_ok=True)
        self._copy_stroke_icons()
        
    def generate_report(self, fit_filename: str = None) -> str:
        """Generate a complete HTML report."""
        # Generate visualizations
        charts = self._generate_charts()
        
        # Load HTML template
        template_path = os.path.join('templates', 'swim_report.html')
        if not os.path.exists(template_path):
            template_content = self._get_default_template()
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        
        # Prepare data for template
        session = self.swim_data.get('session', {})
        summary = self.swim_data.get('summary', {})
        laps = self.swim_data.get('laps', [])
        is_yard_pool = summary.get('is_yard_pool', False)
        
        # Add stroke icons to laps and calculate stroke breakdown
        stroke_breakdown = {}
        for lap in laps:
            stroke_type = lap.get('stroke_type')
            lap['stroke_icon_html'] = get_stroke_icon_html(stroke_type, "48px")
            lap['stroke_icon_small'] = get_stroke_icon_html(stroke_type, "24px")
            lap['stroke_name'] = get_stroke_name(stroke_type)
            
            # Count strokes by type
            if stroke_type:
                stroke_key = stroke_type.lower()
                if stroke_key not in stroke_breakdown:
                    stroke_breakdown[stroke_key] = {
                        'count': 0,
                        'icon_html': get_stroke_icon_html(stroke_type, "64px"),
                        'name': get_stroke_name(stroke_type)
                    }
                stroke_breakdown[stroke_key]['count'] += 1
        
        summary['stroke_breakdown'] = stroke_breakdown
        
        # Generate report HTML
        template = Template(template_content)
        html_content = template.render(
            session=session,
            summary=summary,
            laps=laps,
            charts=charts,
            fit_filename=fit_filename or 'swim_data.fit',
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            get_stroke_icon_html=get_stroke_icon_html,
            get_stroke_name=get_stroke_name
        )
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"swim_report_{timestamp}.html"
        report_path = os.path.join(self.output_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    def generate_multi_workout_report(self, fit_filenames: List[str]) -> str:
        """Generate a tabbed report with multiple workouts and cumulative view."""
        # Process each workout
        workouts = []
        for i, swim_data in enumerate(self.all_swim_data):
            session = swim_data.get('session', {})
            summary = swim_data.get('summary', {})
            laps = swim_data.get('laps', [])
            
            # Add stroke icons to laps
            stroke_breakdown = {}
            for lap in laps:
                stroke_type = lap.get('stroke_type')
                lap['stroke_icon_html'] = get_stroke_icon_html(stroke_type, "48px")
                lap['stroke_icon_small'] = get_stroke_icon_html(stroke_type, "24px")
                lap['stroke_name'] = get_stroke_name(stroke_type)
                
                if stroke_type:
                    stroke_key = stroke_type.lower()
                    if stroke_key not in stroke_breakdown:
                        stroke_breakdown[stroke_key] = {
                            'count': 0,
                            'icon_html': get_stroke_icon_html(stroke_type, "64px"),
                            'name': get_stroke_name(stroke_type)
                        }
                    stroke_breakdown[stroke_key]['count'] += 1
            
            summary['stroke_breakdown'] = stroke_breakdown
            
            # Generate charts for this workout
            charts = self._generate_charts_for_workout(swim_data)
            
            workouts.append({
                'index': i + 1,
                'session': session,
                'summary': summary,
                'laps': laps,
                'charts': charts,
                'filename': fit_filenames[i] if i < len(fit_filenames) else f'workout_{i+1}.fit'
            })
        
        # Generate cumulative data
        cumulative = self._generate_cumulative_data()
        
        # Load multi-workout template
        template_path = os.path.join('templates', 'swim_report_multi.html')
        if not os.path.exists(template_path):
            template_content = self._get_multi_workout_template()
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        
        # Generate report HTML
        template = Template(template_content)
        html_content = template.render(
            workouts=workouts,
            cumulative=cumulative,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            get_stroke_icon_html=get_stroke_icon_html,
            get_stroke_name=get_stroke_name
        )
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"swim_report_multi_{timestamp}.html"
        report_path = os.path.join(self.output_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Also generate PDF
        pdf_path = self._generate_pdf(report_path, html_content)
        
        return report_path, pdf_path
    
    def _generate_charts_for_workout(self, swim_data: Dict) -> Dict[str, str]:
        """Generate charts for a single workout."""
        # Temporarily set swim_data to generate charts
        original_data = self.swim_data
        self.swim_data = swim_data
        charts = self._generate_charts()
        self.swim_data = original_data
        return charts
    
    def _generate_cumulative_data(self) -> Dict:
        """Generate cumulative statistics across all workouts."""
        if len(self.all_swim_data) < 2:
            return {}
        
        total_distance_m = sum(w.get('summary', {}).get('total_distance_m', 0) for w in self.all_swim_data)
        total_distance_yd = sum(w.get('summary', {}).get('total_distance_yd', 0) for w in self.all_swim_data)
        total_time_s = sum(w.get('session', {}).get('total_elapsed_time_s', 0) for w in self.all_swim_data)
        total_strokes = sum(w.get('summary', {}).get('total_strokes', 0) for w in self.all_swim_data)
        total_laps = sum(w.get('summary', {}).get('num_laps', 0) for w in self.all_swim_data)
        
        # Calculate average pace from total distance and time
        if total_time_s > 0 and total_distance_m > 0:
            avg_speed_mps = total_distance_m / total_time_s
            pace_per_100m = self._calculate_pace_from_speed(avg_speed_mps)
            pace_per_100yd = self._calculate_pace_from_speed_yd(avg_speed_mps)
        else:
            # Try to get from individual workouts
            pace_per_100m = None
            pace_per_100yd = None
            for workout in self.all_swim_data:
                w_summary = workout.get('summary', {})
                if w_summary.get('avg_pace_100m') and w_summary.get('avg_pace_100m') != 'N/A':
                    pace_per_100m = w_summary.get('avg_pace_100m')
                if w_summary.get('avg_pace_100yd') and w_summary.get('avg_pace_100yd') != 'N/A':
                    pace_per_100yd = w_summary.get('avg_pace_100yd')
            
            if not pace_per_100m:
                pace_per_100m = 'N/A'
            if not pace_per_100yd:
                pace_per_100yd = 'N/A'
        
        # Check if yard pool (use first workout's setting)
        is_yard_pool = self.all_swim_data[0].get('summary', {}).get('is_yard_pool', False)
        
        # Combine all laps for cumulative view
        all_laps = []
        for i, workout in enumerate(self.all_swim_data):
            for lap in workout.get('laps', []):
                lap_copy = lap.copy()
                lap_copy['workout_number'] = i + 1
                all_laps.append(lap_copy)
        
        # Stroke breakdown across all workouts
        cumulative_stroke_breakdown = {}
        for workout in self.all_swim_data:
            stroke_breakdown = workout.get('summary', {}).get('stroke_breakdown', {})
            for stroke_key, stroke_info in stroke_breakdown.items():
                if stroke_key not in cumulative_stroke_breakdown:
                    cumulative_stroke_breakdown[stroke_key] = {
                        'count': 0,
                        'icon_html': stroke_info.get('icon_html', get_stroke_icon_html(stroke_key, "64px")),
                        'name': stroke_info.get('name', get_stroke_name(stroke_key))
                    }
                cumulative_stroke_breakdown[stroke_key]['count'] += stroke_info.get('count', 0)
        
        return {
            'total_distance_m': total_distance_m,
            'total_distance_yd': total_distance_yd,
            'total_time': self._seconds_to_pace(total_time_s) if total_time_s > 0 else '00:00',
            'total_time_s': total_time_s,
            'total_strokes': total_strokes,
            'total_laps': total_laps,
            'num_workouts': len(self.all_swim_data),
            'avg_pace_100m': pace_per_100m,
            'avg_pace_100yd': pace_per_100yd,
            'avg_pace': pace_per_100yd if is_yard_pool else pace_per_100m,
            'is_yard_pool': is_yard_pool,
            'all_laps': all_laps,
            'stroke_breakdown': cumulative_stroke_breakdown
        }
    
    def _generate_charts(self) -> Dict[str, str]:
        """Generate all charts and return as HTML strings."""
        charts = {}
        
        # Pace over time chart
        if self.swim_data.get('records'):
            charts['pace_chart'] = self._create_pace_chart()
            charts['distance_chart'] = self._create_distance_chart()
            charts['heart_rate_chart'] = self._create_heart_rate_chart()
        
        # Lap analysis chart
        if self.swim_data.get('laps'):
            charts['lap_analysis'] = self._create_lap_analysis_chart()
            charts['lap_pace'] = self._create_lap_pace_chart()
        
        return charts
    
    def _create_pace_chart(self) -> str:
        """Create pace over time chart."""
        records = self.swim_data.get('records', [])
        if not records:
            return ""
        
        df = pd.DataFrame(records)
        if 'timestamp' not in df.columns or df.empty:
            return ""
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Check if yard pool
        summary = self.swim_data.get('summary', {})
        is_yard_pool = summary.get('is_yard_pool', False)
        
        # Check if pace exists, if not try to calculate from speed
        pace_col = 'pace_per_100yd' if is_yard_pool else 'pace_per_100m'
        pace_label = 'Pace per 100 yd' if is_yard_pool else 'Pace per 100m'
        
        if pace_col not in df.columns:
            if 'speed_mps' in df.columns:
                if is_yard_pool:
                    df['pace_per_100yd'] = df['speed_mps'].apply(
                        lambda x: self._calculate_pace_from_speed_yd(x) if x and x > 0 else None
                    )
                else:
                    df['pace_per_100m'] = df['speed_mps'].apply(
                        lambda x: self._calculate_pace_from_speed(x) if x and x > 0 else None
                    )
            else:
                return ""
        
        df = df[df[pace_col].notna()]
        
        if df.empty:
            return ""
        
        # Convert pace from MM:SS string to seconds for plotting
        def pace_to_seconds(pace_str):
            if not pace_str or pace_str == 'N/A':
                return None
            try:
                parts = pace_str.split(':')
                return int(parts[0]) * 60 + int(parts[1])
            except:
                return None
        
        df['pace_seconds'] = df[pace_col].apply(pace_to_seconds)
        df = df[df['pace_seconds'].notna()]
        
        if df.empty:
            return ""
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['pace_seconds'],
            mode='lines+markers',
            name=pace_label,
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4),
            hovertemplate='%{x}<br>Pace: %{customdata}<extra></extra>',
            customdata=[self._seconds_to_pace(s) for s in df['pace_seconds']]
        ))
        
        # Format y-axis ticks as MM:SS
        min_seconds = df['pace_seconds'].min()
        max_seconds = df['pace_seconds'].max()
        tick_interval = max(5, int((max_seconds - min_seconds) / 8))  # ~8 ticks
        tick_vals = list(range(int(min_seconds), int(max_seconds) + tick_interval, tick_interval))
        tick_texts = [self._seconds_to_pace(v) for v in tick_vals]
        
        fig.update_layout(
            title='Pace Over Time',
            xaxis_title='Time',
            yaxis_title=f'Pace (per 100 {"yd" if is_yard_pool else "m"})',
            template='plotly_white',
            height=400,
            hovermode='x unified',
            yaxis=dict(
                tickvals=tick_vals,
                ticktext=tick_texts
            )
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='pace_chart')
    
    def _create_distance_chart(self) -> str:
        """Create cumulative distance chart."""
        records = self.swim_data.get('records', [])
        if not records:
            return ""
        
        df = pd.DataFrame(records)
        if 'timestamp' not in df.columns or 'distance_m' not in df.columns or df.empty:
            return ""
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[df['distance_m'].notna()]
        
        if df.empty:
            return ""
        
        # Check if yard pool
        summary = self.swim_data.get('summary', {})
        is_yard_pool = summary.get('is_yard_pool', False)
        
        if is_yard_pool:
            df['distance_yd'] = df['distance_m'] * 1.09361
            distance_col = 'distance_yd'
            distance_unit = 'yards'
        else:
            distance_col = 'distance_m'
            distance_unit = 'meters'
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df[distance_col],
            mode='lines',
            name='Distance',
            fill='tozeroy',
            line=dict(color='#2ca02c', width=2)
        ))
        
        fig.update_layout(
            title='Cumulative Distance',
            xaxis_title='Time',
            yaxis_title=f'Distance ({distance_unit})',
            template='plotly_white',
            height=400,
            hovermode='x unified'
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='distance_chart')
    
    def _create_heart_rate_chart(self) -> str:
        """Create heart rate chart if available."""
        records = self.swim_data.get('records', [])
        if not records:
            return ""
        
        df = pd.DataFrame(records)
        if 'timestamp' not in df.columns or 'heart_rate' not in df.columns or df.empty:
            return ""
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[df['heart_rate'].notna()]
        
        if df.empty:
            return ""
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['heart_rate'],
            mode='lines+markers',
            name='Heart Rate',
            line=dict(color='#d62728', width=2),
            marker=dict(size=4)
        ))
        
        fig.update_layout(
            title='Heart Rate Over Time',
            xaxis_title='Time',
            yaxis_title='Heart Rate (bpm)',
            template='plotly_white',
            height=400,
            hovermode='x unified'
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='heart_rate_chart')
    
    def _create_lap_analysis_chart(self) -> str:
        """Create lap analysis chart."""
        laps = self.swim_data.get('laps', [])
        if not laps:
            return ""
        
        df = pd.DataFrame(laps)
        summary = self.swim_data.get('summary', {})
        is_yard_pool = summary.get('is_yard_pool', False)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Lap Time', 'Lap Distance', 'Lap Pace', 'Lap Strokes'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Lap Time
        if 'elapsed_time_s' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=list(range(1, len(df) + 1)), 
                    y=df['elapsed_time_s'], 
                    name='Time',
                    hovertemplate='Lap %{x}<br>Time: %{customdata}<extra></extra>',
                    customdata=[self._seconds_to_pace(s) for s in df['elapsed_time_s']]
                ),
                row=1, col=1
            )
            
            # Format y-axis ticks as MM:SS for lap time
            min_time = df['elapsed_time_s'].min()
            max_time = df['elapsed_time_s'].max()
            tick_interval = max(5, int((max_time - min_time) / 6))
            tick_vals = list(range(int(min_time), int(max_time) + tick_interval, tick_interval))
            tick_texts = [self._seconds_to_pace(v) for v in tick_vals]
            fig.update_yaxes(
                tickvals=tick_vals,
                ticktext=tick_texts,
                row=1, col=1
            )
        
        # Lap Distance
        if is_yard_pool and 'distance_yd' in df.columns:
            fig.add_trace(
                go.Bar(x=list(range(1, len(df) + 1)), y=df['distance_yd'], name='Distance (yd)'),
                row=1, col=2
            )
        elif 'distance_m' in df.columns:
            fig.add_trace(
                go.Bar(x=list(range(1, len(df) + 1)), y=df['distance_m'], name='Distance (m)'),
                row=1, col=2
            )
        
        # Lap Pace (convert to seconds for comparison)
        pace_col = 'pace_per_100yd' if is_yard_pool else 'pace_per_100m'
        pace_unit = 's/100yd' if is_yard_pool else 's/100m'
        
        if pace_col in df.columns:
            def pace_to_seconds(pace_str):
                if not pace_str or pace_str == 'N/A':
                    return None
                try:
                    parts = pace_str.split(':')
                    return int(parts[0]) * 60 + int(parts[1])
                except:
                    return None
            
            df['pace_seconds'] = df[pace_col].apply(pace_to_seconds)
            df_pace = df[df['pace_seconds'].notna()]
            if not df_pace.empty:
                fig.add_trace(
                    go.Bar(
                        x=list(range(1, len(df_pace) + 1)), 
                        y=df_pace['pace_seconds'], 
                        name=f'Pace ({pace_unit})',
                        hovertemplate='Lap %{x}<br>Pace: %{customdata}<extra></extra>',
                        customdata=[self._seconds_to_pace(s) for s in df_pace['pace_seconds']]
                    ),
                    row=2, col=1
                )
                
                # Format y-axis ticks as MM:SS for lap pace
                min_pace = df_pace['pace_seconds'].min()
                max_pace = df_pace['pace_seconds'].max()
                tick_interval = max(5, int((max_pace - min_pace) / 6))
                tick_vals = list(range(int(min_pace), int(max_pace) + tick_interval, tick_interval))
                tick_texts = [self._seconds_to_pace(v) for v in tick_vals]
                fig.update_yaxes(
                    tickvals=tick_vals,
                    ticktext=tick_texts,
                    row=2, col=1
                )
        
        # Lap Strokes
        if 'strokes' in df.columns:
            fig.add_trace(
                go.Bar(x=list(range(1, len(df) + 1)), y=df['strokes'], name='Strokes'),
                row=2, col=2
            )
        
        # Update axes labels for all subplots
        distance_unit = 'yards' if is_yard_pool else 'meters'
        
        # Top left: Lap Time
        fig.update_xaxes(title_text='Lap Number', row=1, col=1)
        fig.update_yaxes(title_text='Time (seconds)', row=1, col=1)
        
        # Top right: Lap Distance
        fig.update_xaxes(title_text='Lap Number', row=1, col=2)
        fig.update_yaxes(title_text=f'Distance ({distance_unit})', row=1, col=2)
        
        # Bottom left: Lap Pace
        fig.update_xaxes(title_text='Lap Number', row=2, col=1)
        fig.update_yaxes(title_text=f'Pace (seconds per {pace_unit})', row=2, col=1)
        
        # Bottom right: Lap Strokes
        fig.update_xaxes(title_text='Lap Number', row=2, col=2)
        fig.update_yaxes(title_text='Strokes', row=2, col=2)
        
        fig.update_layout(
            title='Lap Analysis',
            template='plotly_white',
            height=600,
            showlegend=False
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='lap_analysis_chart')
    
    def _create_lap_pace_chart(self) -> str:
        """Create lap pace comparison chart."""
        laps = self.swim_data.get('laps', [])
        if not laps:
            return ""
        
        df = pd.DataFrame(laps)
        if df.empty:
            return ""
        
        summary = self.swim_data.get('summary', {})
        is_yard_pool = summary.get('is_yard_pool', False)
        pace_col = 'pace_per_100yd' if is_yard_pool else 'pace_per_100m'
        pace_unit = '100 yd' if is_yard_pool else '100m'
        
        # Check if pace exists, if not try to calculate from speed
        if pace_col not in df.columns:
            if 'avg_speed_mps' in df.columns:
                if is_yard_pool:
                    df['pace_per_100yd'] = df['avg_speed_mps'].apply(
                        lambda x: self._calculate_pace_from_speed_yd(x) if x and x > 0 else None
                    )
                else:
                    df['pace_per_100m'] = df['avg_speed_mps'].apply(
                        lambda x: self._calculate_pace_from_speed(x) if x and x > 0 else None
                    )
            else:
                return ""
        
        def pace_to_seconds(pace_str):
            if not pace_str or pace_str == 'N/A':
                return None
            try:
                parts = pace_str.split(':')
                return int(parts[0]) * 60 + int(parts[1])
            except:
                return None
        
        df['pace_seconds'] = df[pace_col].apply(pace_to_seconds)
        df = df[df['pace_seconds'].notna()]
        
        if df.empty:
            return ""
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(df) + 1)),
            y=df['pace_seconds'],
            mode='lines+markers',
            name=f'Pace per {pace_unit}',
            line=dict(color='#9467bd', width=3),
            marker=dict(size=8),
            hovertemplate='Lap %{x}<br>Pace: %{customdata}<extra></extra>',
            customdata=[self._seconds_to_pace(s) for s in df['pace_seconds']]
        ))
        
        # Add average line
        avg_pace = df['pace_seconds'].mean()
        fig.add_hline(
            y=avg_pace,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Average: {self._seconds_to_pace(avg_pace)}"
        )
        
        # Format y-axis ticks as MM:SS
        min_pace = df['pace_seconds'].min()
        max_pace = df['pace_seconds'].max()
        tick_interval = max(5, int((max_pace - min_pace) / 8))
        tick_vals = list(range(int(min_pace), int(max_pace) + tick_interval, tick_interval))
        tick_texts = [self._seconds_to_pace(v) for v in tick_vals]
        
        fig.update_layout(
            title='Lap Pace Comparison',
            xaxis_title='Lap Number',
            yaxis_title=f'Pace (per {pace_unit})',
            template='plotly_white',
            height=400,
            hovermode='x unified',
            yaxis=dict(
                tickvals=tick_vals,
                ticktext=tick_texts
            )
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='lap_pace_chart')
    
    def _seconds_to_pace(self, seconds: float) -> str:
        """Convert seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def _calculate_pace_from_speed(self, speed_mps: float) -> str:
        """Calculate pace per 100m from speed in m/s."""
        if speed_mps == 0 or speed_mps is None:
            return None
        pace_seconds = 100 / speed_mps
        return self._seconds_to_pace(pace_seconds)
    
    def _calculate_pace_from_speed_yd(self, speed_mps: float) -> str:
        """Calculate pace per 100 yards from speed in m/s."""
        if speed_mps == 0 or speed_mps is None:
            return None
        # Convert m/s to yards/s, then calculate pace per 100 yards
        speed_ydps = speed_mps * 1.09361
        pace_seconds = 100 / speed_ydps
        return self._seconds_to_pace(pace_seconds)
    
    def _copy_stroke_icons(self):
        """Copy stroke icon files to reports/icons directory."""
        source_icons_dir = 'icons/strokes'
        if not os.path.exists(source_icons_dir):
            source_icons_dir = 'icons'
        
        # Copy all image files from source to destination
        if os.path.exists(source_icons_dir):
            for filename in os.listdir(source_icons_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.avif', '.gif')):
                    src = os.path.join(source_icons_dir, filename)
                    dst = os.path.join(self.icons_dir, filename)
                    try:
                        shutil.copy2(src, dst)
                    except Exception as e:
                        print(f"Warning: Could not copy icon {filename}: {e}")
    
    def _get_multi_workout_template(self) -> str:
        """Get default multi-workout HTML template."""
        # Return empty string - we'll use the file template
        return ""
    
    def _generate_pdf(self, html_path: str, html_content: str) -> str:
        """Generate PDF from HTML report using Playwright."""
        try:
            from playwright.sync_api import sync_playwright
            
            pdf_path = html_path.replace('.html', '.pdf')
            abs_html_path = os.path.abspath(html_path)
            abs_pdf_path = os.path.abspath(pdf_path)
            
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                
                # Load the HTML file
                page.goto(f'file:///{abs_html_path.replace(os.sep, "/")}')
                
                # Wait for charts to load (Plotly charts need time to render)
                page.wait_for_timeout(3000)  # Wait 3 seconds for charts
                
                # Generate PDF
                page.pdf(
                    path=abs_pdf_path,
                    format='A4',
                    landscape=True,
                    margin={'top': '1cm', 'right': '1cm', 'bottom': '1cm', 'left': '1cm'},
                    print_background=True
                )
                
                browser.close()
            
            return pdf_path
        except ImportError:
            print("⚠️  Warning: playwright not installed. PDF generation skipped.")
            print("   Install with: pip install playwright")
            print("   Then run: playwright install chromium")
            return None
        except Exception as e:
            print(f"⚠️  Warning: Could not generate PDF: {str(e)}")
            print("   Make sure playwright browsers are installed: playwright install chromium")
            return None
    
    def _get_default_template(self) -> str:
        """Get default HTML template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Swim Report - {{ session.date or 'Swim Session' }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .summary-card:hover {
            transform: translateY(-5px);
        }
        
        .summary-card h3 {
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        
        .section {
            margin-bottom: 50px;
        }
        
        .section h2 {
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        
        .chart-container {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .laps-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .laps-table th,
        .laps-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .laps-table th {
            background: #667eea;
            color: white;
            font-weight: 600;
        }
        
        .laps-table tr:hover {
            background: #f5f5f5;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏊 Swim Session Report</h1>
            <p>{{ session.date or 'Swim Session' }} at {{ session.time or 'N/A' }}</p>
        </div>
        
        <div class="content">
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Total Distance</h3>
                    <div class="value">{{ "%.0f"|format(summary.total_distance_m) }}m</div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
                        {{ "%.0f"|format(summary.total_distance_yd) }} yards
                    </div>
                </div>
                
                <div class="summary-card">
                    <h3>Total Time</h3>
                    <div class="value">{{ summary.total_time }}</div>
                </div>
                
                <div class="summary-card">
                    <h3>Average Pace</h3>
                    <div class="value">{{ summary.avg_pace }}</div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 5px;">per 100m</div>
                </div>
                
                <div class="summary-card">
                    <h3>Total Strokes</h3>
                    <div class="value">{{ summary.total_strokes }}</div>
                    {% if summary.strokes_per_length %}
                    <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
                        {{ summary.strokes_per_length }} per length
                    </div>
                    {% endif %}
                </div>
                
                <div class="summary-card">
                    <h3>Number of Laps</h3>
                    <div class="value">{{ summary.num_laps }}</div>
                </div>
                
                <div class="summary-card">
                    <h3>Pool Length</h3>
                    <div class="value">{{ "%.0f"|format(summary.pool_length) }}m</div>
                </div>
            </div>
            
            {% if charts.pace_chart %}
            <div class="section">
                <h2>Performance Charts</h2>
                <div class="chart-container">
                    {{ charts.pace_chart|safe }}
                </div>
            </div>
            {% endif %}
            
            {% if charts.distance_chart %}
            <div class="section">
                <div class="chart-container">
                    {{ charts.distance_chart|safe }}
                </div>
            </div>
            {% endif %}
            
            {% if charts.heart_rate_chart %}
            <div class="section">
                <div class="chart-container">
                    {{ charts.heart_rate_chart|safe }}
                </div>
            </div>
            {% endif %}
            
            {% if charts.lap_analysis %}
            <div class="section">
                <h2>Lap Analysis</h2>
                <div class="chart-container">
                    {{ charts.lap_analysis|safe }}
                </div>
            </div>
            {% endif %}
            
            {% if charts.lap_pace %}
            <div class="section">
                <div class="chart-container">
                    {{ charts.lap_pace|safe }}
                </div>
            </div>
            {% endif %}
            
            {% if laps %}
            <div class="section">
                <h2>Lap Details</h2>
                <table class="laps-table">
                    <thead>
                        <tr>
                            <th>Lap</th>
                            <th>Time</th>
                            <th>Distance</th>
                            <th>Pace</th>
                            <th>Strokes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for lap in laps %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td>{{ lap.time_formatted or 'N/A' }}</td>
                            <td>{{ "%.0f"|format(lap.distance_m) if lap.distance_m else 'N/A' }}m</td>
                            <td>{{ lap.pace_per_100m or 'N/A' }}</td>
                            <td>{{ lap.strokes or lap.stroke_count or 'N/A' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>Generated on {{ generated_at }} from {{ fit_filename }}</p>
        </div>
    </div>
</body>
</html>"""

