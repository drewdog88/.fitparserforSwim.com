"""
FIT file parser for extracting swim data from Garmin FIT files.
"""
import fitdecode
from datetime import datetime
from typing import Dict, List, Optional
import json


class FITParser:
    """Parser for Garmin FIT files containing swim data."""
    
    def __init__(self, fit_file_path: str):
        self.fit_file_path = fit_file_path
        self.data = {}
        
    def parse(self) -> Dict:
        """Parse the FIT file and extract swim data."""
        try:
            with fitdecode.FitReader(self.fit_file_path) as fit:
                session_data = {}
                lap_data = []
                length_data = []
                record_data = []
                
                for frame in fit:
                    if frame.frame_type == fitdecode.FIT_FRAME_DATA:
                        # Process session data
                        if frame.name == 'session':
                            session_data = self._extract_session_data(frame)
                        
                        # Process lap data
                        elif frame.name == 'lap':
                            lap = self._extract_lap_data(frame)
                            if lap:
                                lap_data.append(lap)
                        
                        # Process length data (individual pool lengths)
                        elif frame.name == 'length':
                            length = self._extract_length_data(frame)
                            if length:
                                length_data.append(length)
                        
                        # Process record data (detailed track points)
                        elif frame.name == 'record':
                            record = self._extract_record_data(frame)
                            if record:
                                record_data.append(record)
                
                self.data = {
                    'session': session_data,
                    'laps': lap_data,
                    'lengths': length_data,
                    'records': record_data,
                    'summary': self._generate_summary(session_data, lap_data, length_data, record_data)
                }
                
                return self.data
                
        except Exception as e:
            raise Exception(f"Error parsing FIT file: {str(e)}")
    
    def _extract_session_data(self, frame) -> Dict:
        """Extract session-level data."""
        session = {}
        
        for field in frame.fields:
            field_name = field.name
            field_value = field.value
            
            # Convert timestamp to readable format
            if field_name == 'timestamp':
                if isinstance(field_value, datetime):
                    session['timestamp'] = field_value.isoformat()
                    session['date'] = field_value.strftime('%Y-%m-%d')
                    session['time'] = field_value.strftime('%H:%M:%S')
                else:
                    session['timestamp'] = str(field_value)
            
            # Distance in meters (FIT files always store in meters)
            elif field_name == 'total_distance':
                session['total_distance_m'] = float(field_value) if field_value else 0
                session['total_distance_yd'] = session['total_distance_m'] * 1.09361
                session['total_distance_mi'] = session['total_distance_m'] * 0.000621371
            
            # Time in seconds
            elif field_name == 'total_elapsed_time':
                session['total_elapsed_time_s'] = float(field_value) if field_value else 0
                session['total_time_formatted'] = self._format_time(session['total_elapsed_time_s'])
            
            # Active timer time (swim time without rest)
            elif field_name == 'total_timer_time':
                session['total_timer_time_s'] = float(field_value) if field_value else 0
                session['active_time_formatted'] = self._format_time(session['total_timer_time_s'])
            
            # Number of active lengths (what user sees as "laps")
            elif field_name == 'num_active_lengths':
                session['num_active_lengths'] = int(field_value) if field_value else 0
            
            # Average pace
            elif field_name == 'avg_speed':
                session['avg_speed_mps'] = float(field_value) if field_value else 0
                session['avg_pace_per_100m'] = self._calculate_pace(session['avg_speed_mps'])
                # Also calculate pace per 100 yards
                session['avg_pace_per_100yd'] = self._calculate_pace_per_100yd(session['avg_speed_mps'])
            
            # Stroke data
            elif field_name == 'total_strokes':
                session['total_strokes'] = int(field_value) if field_value else 0
            
            # Pool length
            elif field_name == 'pool_length':
                pool_length_m = float(field_value) if field_value else 0
                session['pool_length_m'] = pool_length_m
                # Convert to yards
                session['pool_length_yd'] = pool_length_m * 1.09361
                
                # Detect if pool is in yards (common lengths: 25yd=22.86m, 50yd=45.72m)
                # Check if pool_length_m is close to a standard yard pool length
                yard_pool_lengths = {
                    22.86: 25,   # 25 yards
                    45.72: 50,   # 50 yards
                    27.43: 30,   # 30 yards (less common)
                }
                
                # Check if within 0.5m of a standard yard pool length
                is_yard_pool = False
                for meters, yards in yard_pool_lengths.items():
                    if abs(pool_length_m - meters) < 0.5:
                        session['pool_length_yd'] = yards
                        session['is_yard_pool'] = True
                        is_yard_pool = True
                        break
                
                if not is_yard_pool:
                    # Check if it's a common meter pool (25m, 50m)
                    if abs(pool_length_m - 25.0) < 0.5 or abs(pool_length_m - 50.0) < 0.5:
                        session['is_yard_pool'] = False
                    else:
                        # Default: assume meters if unclear
                        session['is_yard_pool'] = False
            
            # Calories
            elif field_name == 'total_calories':
                session['total_calories'] = int(field_value) if field_value else 0
            
            # Heart rate
            elif field_name == 'avg_heart_rate':
                session['avg_heart_rate'] = int(field_value) if field_value else None
            elif field_name == 'max_heart_rate':
                session['max_heart_rate'] = int(field_value) if field_value else None
            
            # Swim type
            elif field_name == 'sport':
                session['sport'] = str(field_value) if field_value else 'swimming'
            
            # Number of lengths
            elif field_name == 'num_lengths':
                session['num_lengths'] = int(field_value) if field_value else 0
            
            # Number of laps (different from lengths)
            elif field_name == 'num_laps':
                session['num_laps_session'] = int(field_value) if field_value else 0
        
        return session
    
    def _extract_lap_data(self, frame) -> Optional[Dict]:
        """Extract lap-level data."""
        lap = {}
        
        for field in frame.fields:
            field_name = field.name
            field_value = field.value
            
            if field_name == 'timestamp':
                if isinstance(field_value, datetime):
                    lap['timestamp'] = field_value.isoformat()
                else:
                    lap['timestamp'] = str(field_value)
            
            elif field_name == 'total_elapsed_time':
                lap['elapsed_time_s'] = float(field_value) if field_value else 0
                lap['time_formatted'] = self._format_time(lap['elapsed_time_s'])
            
            elif field_name == 'total_distance':
                lap['distance_m'] = float(field_value) if field_value else 0
                lap['distance_yd'] = lap['distance_m'] * 1.09361
            
            elif field_name == 'avg_speed':
                lap['avg_speed_mps'] = float(field_value) if field_value else 0
                lap['pace_per_100m'] = self._calculate_pace(lap['avg_speed_mps'])
                lap['pace_per_100yd'] = self._calculate_pace_per_100yd(lap['avg_speed_mps'])
            
            elif field_name == 'total_strokes':
                lap['strokes'] = int(field_value) if field_value else 0
            
            elif field_name == 'stroke_count':
                lap['stroke_count'] = int(field_value) if field_value else 0
            
            # Stroke type
            elif field_name == 'swim_stroke':
                lap['stroke_type'] = str(field_value).lower() if field_value else None
        
        # Calculate pace from distance and time if avg_speed not available
        if 'pace_per_100m' not in lap or not lap.get('pace_per_100m'):
            if lap.get('distance_m', 0) > 0 and lap.get('elapsed_time_s', 0) > 0:
                # Calculate speed from distance and time
                lap_speed_mps = lap['distance_m'] / lap['elapsed_time_s']
                lap['avg_speed_mps'] = lap_speed_mps
                lap['pace_per_100m'] = self._calculate_pace(lap_speed_mps)
                lap['pace_per_100yd'] = self._calculate_pace_per_100yd(lap_speed_mps)
        
        return lap if lap else None
    
    def _extract_length_data(self, frame) -> Optional[Dict]:
        """Extract length-level data (individual pool lengths)."""
        length = {}
        
        for field in frame.fields:
            field_name = field.name
            field_value = field.value
            
            if field_name == 'timestamp':
                if isinstance(field_value, datetime):
                    length['timestamp'] = field_value.isoformat()
                else:
                    length['timestamp'] = str(field_value)
            
            elif field_name == 'total_elapsed_time':
                length['elapsed_time_s'] = float(field_value) if field_value else 0
                length['time_formatted'] = self._format_time(length['elapsed_time_s'])
            
            elif field_name == 'total_timer_time':
                length['timer_time_s'] = float(field_value) if field_value else 0
            
            elif field_name == 'total_distance':
                length['distance_m'] = float(field_value) if field_value else 0
                length['distance_yd'] = length['distance_m'] * 1.09361
            
            elif field_name == 'swim_stroke':
                length['stroke_type'] = str(field_value).lower() if field_value else None
            
            elif field_name == 'length_type':
                length['length_type'] = str(field_value).lower() if field_value else None
                length['is_active'] = (str(field_value).lower() == 'active')
        
        return length if length else None
    
    def _extract_record_data(self, frame) -> Optional[Dict]:
        """Extract record-level (track point) data."""
        record = {}
        
        for field in frame.fields:
            field_name = field.name
            field_value = field.value
            
            if field_name == 'timestamp':
                if isinstance(field_value, datetime):
                    record['timestamp'] = field_value.isoformat()
                else:
                    record['timestamp'] = str(field_value)
            
            elif field_name == 'distance':
                record['distance_m'] = float(field_value) if field_value else 0
            
            elif field_name == 'speed':
                record['speed_mps'] = float(field_value) if field_value else 0
                record['pace_per_100m'] = self._calculate_pace(record['speed_mps'])
            
            elif field_name == 'heart_rate':
                record['heart_rate'] = int(field_value) if field_value else None
        
        return record if record else None
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into H:MM:SS or MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _calculate_pace(self, speed_mps: float) -> Optional[str]:
        """Calculate pace per 100m from speed in m/s."""
        if speed_mps == 0:
            return None
        pace_seconds = 100 / speed_mps
        return self._format_time(pace_seconds)
    
    def _calculate_pace_per_100yd(self, speed_mps: float) -> Optional[str]:
        """Calculate pace per 100 yards from speed in m/s."""
        if speed_mps == 0:
            return None
        # Convert m/s to yards/s, then calculate pace per 100 yards
        speed_ydps = speed_mps * 1.09361
        pace_seconds = 100 / speed_ydps
        return self._format_time(pace_seconds)
    
    def _generate_summary(self, session: Dict, laps: List[Dict], lengths: List[Dict], records: List[Dict]) -> Dict:
        """Generate summary statistics."""
        is_yard_pool = session.get('is_yard_pool', False)
        
        # Calculate average pace from total distance and ACTIVE time (not total elapsed)
        total_distance_m = session.get('total_distance_m', 0)
        total_distance_yd = session.get('total_distance_yd', 0)
        total_time_s = session.get('total_elapsed_time_s', 0)
        
        # Calculate active swim time from ACTIVE length records only
        # Use length_type field to identify active vs idle (rest) lengths
        num_active_lengths = session.get('num_active_lengths', 0)
        
        active_time_s = 0
        if lengths:
            # Sum elapsed times from only the active lengths (length_type == 'active')
            # Length elapsed_time is per-length (swimming time for that length)
            active_lengths = [l for l in lengths if l.get('is_active', False) or l.get('length_type') == 'active']
            
            if active_lengths:
                active_time_s = sum(length.get('elapsed_time_s', 0) for length in active_lengths)
                # Update num_active_lengths from actual count
                if num_active_lengths == 0:
                    num_active_lengths = len(active_lengths)
            else:
                # Fallback: if no length_type field, use first num_active_lengths
                if num_active_lengths > 0:
                    active_lengths = lengths[:num_active_lengths]
                    active_time_s = sum(length.get('elapsed_time_s', 0) for length in active_lengths)
        
        # Fall back to session total_timer_time if still 0
        if active_time_s == 0:
            active_time_s = session.get('total_timer_time_s', 0)
        
        # Use active time for pace calculation
        swim_time_s = active_time_s if active_time_s > 0 else total_time_s
        
        avg_pace_100m = session.get('avg_pace_per_100m')
        avg_pace_100yd = session.get('avg_pace_per_100yd')
        
        # Try to calculate average pace from lap paces first (more accurate)
        # This matches what swim.com app shows
        if laps and is_yard_pool:
            # Get all lap paces in yards
            lap_paces_yd = []
            for lap in laps:
                if lap.get('pace_per_100yd'):
                    pace_str = lap['pace_per_100yd']
                    # Convert MM:SS to seconds
                    try:
                        parts = pace_str.split(':')
                        if len(parts) == 2:
                            pace_seconds = int(parts[0]) * 60 + int(parts[1])
                            lap_paces_yd.append(pace_seconds)
                    except:
                        pass
            
            if lap_paces_yd:
                avg_pace_seconds_yd = sum(lap_paces_yd) / len(lap_paces_yd)
                avg_pace_100yd = self._format_time(avg_pace_seconds_yd)
        
        elif laps and not is_yard_pool:
            # Get all lap paces in meters
            lap_paces_m = []
            for lap in laps:
                if lap.get('pace_per_100m'):
                    pace_str = lap['pace_per_100m']
                    # Convert MM:SS to seconds
                    try:
                        parts = pace_str.split(':')
                        if len(parts) == 2:
                            pace_seconds = int(parts[0]) * 60 + int(parts[1])
                            lap_paces_m.append(pace_seconds)
                    except:
                        pass
            
            if lap_paces_m:
                avg_pace_seconds_m = sum(lap_paces_m) / len(lap_paces_m)
                avg_pace_100m = self._format_time(avg_pace_seconds_m)
        
        # If pace not calculated from lap paces or avg_speed, calculate from distance/active_time
        if not avg_pace_100m and total_distance_m > 0 and swim_time_s > 0:
            avg_speed_mps = total_distance_m / swim_time_s
            avg_pace_100m = self._calculate_pace(avg_speed_mps)
            if not avg_pace_100yd:
                avg_pace_100yd = self._calculate_pace_per_100yd(avg_speed_mps)
        
        # Use num_active_lengths (what user sees) instead of num_laps
        num_active_lengths = session.get('num_active_lengths', 0)
        if num_active_lengths == 0:
            num_active_lengths = len(lengths) if lengths else len(laps)
        num_lengths_display = num_active_lengths
        
        # Calculate rest time
        rest_time_s = total_time_s - active_time_s if active_time_s > 0 and total_time_s > active_time_s else 0
        
        # Format active time
        active_time_formatted = self._format_time(active_time_s) if active_time_s > 0 else session.get('active_time_formatted', '00:00')
        
        summary = {
            'total_distance_m': total_distance_m,
            'total_distance_yd': session.get('total_distance_yd', 0),
            'total_time': session.get('total_time_formatted', '00:00'),
            'active_time': active_time_formatted,
            'rest_time': self._format_time(rest_time_s) if rest_time_s > 0 else '00:00',
            'total_strokes': session.get('total_strokes', 0),
            'num_laps': num_lengths_display,  # Use active lengths for display
            'num_laps_actual': len(laps),  # Keep actual lap count
            'num_records': len(records),
            'avg_pace': avg_pace_100yd if is_yard_pool else avg_pace_100m if avg_pace_100m else 'N/A',
            'avg_pace_100m': avg_pace_100m if avg_pace_100m else 'N/A',
            'avg_pace_100yd': avg_pace_100yd if avg_pace_100yd else 'N/A',
            'pool_length_m': session.get('pool_length_m', 0),
            'pool_length_yd': session.get('pool_length_yd', 0),
            'pool_length': session.get('pool_length_yd' if is_yard_pool else 'pool_length_m', 0),
            'is_yard_pool': is_yard_pool,
            'num_lengths': session.get('num_lengths', 0),
            'num_active_lengths': num_active_lengths,
        }
        
        # Calculate strokes per length if available
        if summary['num_lengths'] > 0 and summary['total_strokes'] > 0:
            summary['strokes_per_length'] = round(summary['total_strokes'] / summary['num_lengths'], 1)
        
        # Calculate average strokes per lap
        if laps and summary['total_strokes'] > 0:
            summary['avg_strokes_per_lap'] = round(summary['total_strokes'] / len(laps), 1)
        
        return summary
    
    def get_data(self) -> Dict:
        """Get parsed data."""
        return self.data
    
    def export_json(self, output_path: str):
        """Export parsed data to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=2)

