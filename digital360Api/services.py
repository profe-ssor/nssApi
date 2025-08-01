from django.utils import timezone
from .models import GhanaCardRecord, UniversityRecord, GhostDetection
from nss_personnel.models import NSSPersonnel, ArchivedNSSPersonnel
from nss_admin.models import Administrator
from messageApp.models import Message
from nss_supervisors.models import ActivityLog

def detect_ghost_personnel(personnel_id):
    """
    Detect ghost personnel by personnel ID or user ID
    Returns a dictionary with detection results
    """
    print(f"[DEBUG] detect_ghost_personnel called with personnel_id: {personnel_id} (type: {type(personnel_id)})")
    try:
        # Try by NSSPersonnel.id first
        personnel = NSSPersonnel.objects.get(id=personnel_id)
        print(f"[DEBUG] Found personnel by id: {personnel}")
        
        # Run ghost detection
        ghost_flags = detect_ghost_personnel_during_submission(personnel)
        
        # Determine if it's a ghost
        is_ghost = len(ghost_flags) > 0
        
        # Calculate severity
        severity = calculate_severity(ghost_flags)
        
        return {
            'is_ghost': is_ghost,
            'personnel_id': personnel_id,
            'personnel_name': personnel.full_name,
            'ghana_card_number': personnel.ghana_card_record,
            'flags': ghost_flags,
            'severity': severity,
            'reason': '; '.join(ghost_flags) if ghost_flags else 'No issues detected',
            'personnel_obj': personnel
        }
        
    except NSSPersonnel.DoesNotExist:
        print(f"[DEBUG] No personnel found by id: {personnel_id}, trying user_id...")
        try:
            # Try by user_id if not found by id
            personnel = NSSPersonnel.objects.get(user_id=personnel_id)
            print(f"[DEBUG] Found personnel by user_id: {personnel}")
            # Run ghost detection
            ghost_flags = detect_ghost_personnel_during_submission(personnel)
            is_ghost = len(ghost_flags) > 0
            severity = calculate_severity(ghost_flags)
            return {
                'is_ghost': is_ghost,
                'personnel_id': personnel_id,
                'personnel_name': personnel.full_name,
                'ghana_card_number': personnel.ghana_card_record,
                'flags': ghost_flags,
                'severity': severity,
                'reason': '; '.join(ghost_flags) if ghost_flags else 'No issues detected',
                'personnel_obj': personnel
            }
        except NSSPersonnel.DoesNotExist:
            print(f"[DEBUG] No personnel found by user_id: {personnel_id}")
            return {
                'is_ghost': True,
                'personnel_id': personnel_id,
                'personnel_name': 'Unknown',
                'ghana_card_number': '',
                'flags': ['❌ Personnel not found in NSS database'],
                'severity': 'critical',
                'reason': 'Personnel not found in NSS database'
            }
    except Exception as e:
        print(f"[ERROR] Exception in detect_ghost_personnel: {e}")
        return {
            'is_ghost': False,
            'personnel_id': personnel_id,
            'personnel_name': 'Error',
            'ghana_card_number': '',
            'flags': [f'❌ Error during detection: {str(e)}'],
            'severity': 'error',
            'reason': f'Error during detection: {str(e)}'
        }

def detect_ghost_personnel_during_submission(nss_personnel):
    """
    Comprehensive ghost detection using CharField ghana_card_record
    Now more robust: ignores case and whitespace for name/contact checks.
    """
    ghost_flags = []
    
    # 1. Check Ghana Card Records Database
    ghana_card_record = GhanaCardRecord.objects.filter(
        ghana_card_number=nss_personnel.ghana_card_record
    ).first()
    
    if not ghana_card_record:
        ghost_flags.append("❌ Ghana Card not found in official records")
    else:
        # Check name consistency (ignore case and whitespace)
        personnel_name = nss_personnel.full_name.strip().lower()
        card_name = ghana_card_record.full_name.strip().lower()
        if card_name != personnel_name:
            ghost_flags.append("⚠️ Name mismatch with Ghana Card records")
        
        # Check other details (ignore whitespace)
        personnel_phone = (nss_personnel.phone or '').replace(' ', '')
        card_phone = (ghana_card_record.contact_number or '').replace(' ', '')
        if card_phone != personnel_phone:
            ghost_flags.append("⚠️ Contact number mismatch")
    
    # 2. Check University Records Database
    if ghana_card_record:
        university_record = UniversityRecord.objects.filter(
            ghana_card_number=ghana_card_record
        ).first()
        
        if not university_record:
            ghost_flags.append("❌ No university record found")
        else:
            uni_name = university_record.full_name.strip().lower()
            if uni_name != personnel_name:
                ghost_flags.append("⚠️ Name mismatch with university records")
    
    # 3. Check for Duplicate NSS Personnel
    duplicate_nss = NSSPersonnel.objects.filter(
        ghana_card_record=nss_personnel.ghana_card_record
    ).exclude(id=nss_personnel.id)
    
    if duplicate_nss.exists():
        ghost_flags.append("🚨 Duplicate NSS personnel with same Ghana Card")
    
    # 4. Check for Multiple Active Personnel
    active_personnel = NSSPersonnel.objects.filter(
        ghana_card_record=nss_personnel.ghana_card_record,
        status='active'
    ).exclude(id=nss_personnel.id)
    
    if active_personnel.exists():
        ghost_flags.append("🚨 Multiple active personnel with same Ghana Card")
    
    # 5. Check for archived personnel
    if ArchivedNSSPersonnel.objects.filter(ghana_card_record=nss_personnel.ghana_card_record).exists():
        ghost_flags.append("🚩 Ghana Card ID found in archive (Completed Service) - submission blocked")
    
    return ghost_flags

def calculate_severity(ghost_flags):
    """Calculate severity based on flags"""
    if any('🚨' in flag for flag in ghost_flags):
        return 'critical'
    elif any('❌' in flag for flag in ghost_flags):
        return 'high'
    elif any('⚠️' in flag for flag in ghost_flags):
        return 'medium'
    return 'low'

def send_ghost_alert_to_admin(ghost_detection):
    """
    Send immediate alert to ALL ADMINISTRATORS about ghost detection
    """
    personnel = ghost_detection.nss_personnel
    supervisor = ghost_detection.supervisor
    
    # Get all administrators
    administrators = Administrator.objects.all()
    
    for admin in administrators:
        # Create urgent message for each admin
        message = Message.objects.create(
            sender=admin.user,  # System message
            receiver=admin.user,
            subject=f"🚨 CRITICAL: GHOST PERSONNEL DETECTED - {personnel.full_name}",
            content=f"""
            🚨 CRITICAL GHOST PERSONNEL DETECTION ALERT! 🚨
            
            Personnel Details:
            • Name: {personnel.full_name}
            • Ghana Card: {personnel.ghana_card_record}
            • NSS ID: {personnel.nss_id}
            • Status: {personnel.status}
            • Assigned Supervisor: {supervisor.full_name}
            • Region: {personnel.region_of_posting}
            • Department: {personnel.department}
            
            Detection Flags:
            {chr(10).join([f"• {flag}" for flag in ghost_detection.detection_flags])}
            
            Severity: {ghost_detection.severity.upper()}
            Detection Time: {ghost_detection.timestamp}
            Submission Attempt: {'YES' if ghost_detection.submission_attempt else 'NO'}
            
            IMMEDIATE ADMIN ACTION REQUIRED:
            1. Investigate personnel authenticity
            2. Verify Ghana Card records
            3. Check university records
            4. Review supervisor assignment
            5. Take appropriate disciplinary action
            
            This is a HIGH PRIORITY security alert!
            """,
            priority='high',
            message_type='report'
        )
        
        # Log admin activity
        ActivityLog.objects.create(
            supervisor=admin.user,  # Using supervisor field for admin
            action='admin_ghost_detection',
            title=f"Admin Ghost Alert: {personnel.full_name}",
            description=f"Flags: {', '.join(ghost_detection.detection_flags)}",
            personnel=personnel.full_name,
            priority='high'
        )
    
    # Also notify the assigned supervisor (for awareness)
    supervisor_message = Message.objects.create(
        sender=supervisor.user,
        receiver=supervisor.user,
        subject=f"⚠️ GHOST PERSONNEL ALERT: {personnel.full_name}",
        content=f"""
        ⚠️ GHOST PERSONNEL DETECTION NOTIFICATION
        
        Your assigned personnel has been flagged for ghost detection:
        
        Personnel: {personnel.full_name}
        Ghana Card: {personnel.ghana_card_record}
        
        Detection Flags:
        {chr(10).join([f"• {flag}" for flag in ghost_detection.detection_flags])}
        
        Administrators have been notified and will investigate.
        Please cooperate with any investigation requests.
        """,
        priority='medium',
        message_type='report'
    ) 