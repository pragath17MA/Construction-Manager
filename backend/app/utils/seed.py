import os
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import database session & models
from app.core.database import Base, engine
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.project import Project, ProjectMember, Document, Drawing, SiteImage
from app.models.budget import Budget, BudgetItem, EquipmentCost, LaborCost
from app.models.material import Material, Inventory, Supplier, PurchaseOrder
from app.models.worker import Worker, WorkerSkill, WorkerSchedule, Attendance, LeaveRequest, ShiftPlan
from app.models.risk import Risk, RiskHistory, WeatherData, DelayPrediction
from app.models.progress import Milestone, ProgressReport, DailyLog
from app.models.invoice import Invoice, InvoiceItem, InvoiceComparison, OCRLog
from app.models.image_analysis import SiteImageAnalysis
from app.models.voice import VoiceCommandLog
from app.models.chat import ChatSession, ChatMessage

def clean_database(db: Session):
    """Clean all tables in the database."""
    # SQLite foreign keys check disabled temporarily during truncation
    db.execute(text("PRAGMA foreign_keys = OFF;"))
    db.commit()
    
    tables = [
        "ocr_logs", "invoice_comparisons", "invoice_items", "invoices",
        "site_image_analyses", "site_images", "drawings", "documents",
        "daily_logs", "progress_reports", "milestones",
        "delay_predictions", "weather_datas", "risk_histories", "risks",
        "worker_schedules", "leave_requests", "attendance", "worker_skills", "workers",
        "shift_plans", "purchase_orders", "suppliers", "inventory", "materials",
        "labor_costs", "equipment_costs", "budget_items", "budgets",
        "project_members", "projects", "users", "voice_command_logs",
        "chat_messages", "chat_sessions"
    ]
    for t in tables:
        try:
            db.execute(text(f"DELETE FROM [{t}];"))
        except Exception as e:
            print(f"Error truncating table {t}: {e}")
    db.commit()
    db.execute(text("PRAGMA foreign_keys = ON;"))
    db.commit()

def run_seed(db: Session):
    """Seed structured operational mock data."""
    print("Truncating existing tables...")
    clean_database(db)
    
    print("Creating core users...")
    hashed_pwd = get_password_hash("Password123")
    
    admin = User(
        email="admin@example.com",
        hashed_password=hashed_pwd,
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    pm = User(
        email="pm@example.com",
        hashed_password=hashed_pwd,
        full_name="Project Manager PM",
        role=UserRole.PROJECT_MANAGER,
        is_active=True
    )
    engineer = User(
        email="engineer@example.com",
        hashed_password=hashed_pwd,
        full_name="Site Engineer SE",
        role=UserRole.SITE_ENGINEER,
        is_active=True
    )
    
    db.add_all([admin, pm, engineer])
    db.commit()
    db.refresh(admin)
    db.refresh(pm)
    db.refresh(engineer)
    
    print("Seeding construction projects...")
    today = date.today()
    
    proj1 = Project(
        project_name="Apex Commercial Tower",
        description="Modern 15-story commercial skyscraper with sustainable features and double-skin glass facade.",
        client_name="Apex Infra Development",
        location="Mumbai, IN",
        start_date=today - timedelta(days=90),
        expected_end_date=today + timedelta(days=270),
        status="In Progress",
        budget=Decimal("50000000.00"),
        created_by=admin.id
    )
    
    proj2 = Project(
        project_name="Metro Overpass Section 4",
        description="Construction of a 2.4 km elevated rapid transit viaduct segment involving precast segmental box girders.",
        client_name="Urban Transit Authority",
        location="Bangalore, IN",
        start_date=today + timedelta(days=30),
        expected_end_date=today + timedelta(days=395),
        status="Planning",
        budget=Decimal("120000000.00"),
        created_by=admin.id
    )
    
    proj3 = Project(
        project_name="Substation Grid Upgrade",
        description="Expansion and refurbishment of the existing 400kV gas insulated substation to increase transmission load limits.",
        client_name="National Power Corp",
        location="Delhi, IN",
        start_date=today - timedelta(days=120),
        expected_end_date=today - timedelta(days=10),
        status="Delayed",
        budget=Decimal("18000000.00"),
        created_by=admin.id
    )
    
    db.add_all([proj1, proj2, proj3])
    db.commit()
    db.refresh(proj1)
    db.refresh(proj2)
    db.refresh(proj3)
    
    print("Setting project memberships...")
    mem1 = ProjectMember(project_id=proj1.id, user_id=pm.id, role=UserRole.PROJECT_MANAGER)
    mem2 = ProjectMember(project_id=proj1.id, user_id=engineer.id, role=UserRole.SITE_ENGINEER)
    mem3 = ProjectMember(project_id=proj2.id, user_id=pm.id, role=UserRole.PROJECT_MANAGER)
    mem4 = ProjectMember(project_id=proj3.id, user_id=pm.id, role=UserRole.PROJECT_MANAGER)
    mem5 = ProjectMember(project_id=proj3.id, user_id=engineer.id, role=UserRole.SITE_ENGINEER)
    db.add_all([mem1, mem2, mem3, mem4, mem5])
    db.commit()
    
    print("Registering professional workers pool...")
    workers_data = [
        ("Karan Sharma", "karan@example.com", "9876543210", "Supervisor", "Skilled", 1500.00),
        ("Rahul Verma", "rahul@example.com", "9876543211", "Mason", "Skilled", 1000.00),
        ("Amit Patel", "amit@example.com", "9876543212", "Mason", "Semi-Skilled", 800.00),
        ("Vijay Singh", "vijay@example.com", "9876543213", "Electrician", "Skilled", 1200.00),
        ("Rajesh Kumar", "rajesh@example.com", "9876543214", "Plumber", "Skilled", 1100.00),
        ("Suresh Yadav", "suresh@example.com", "9876543215", "Operator", "Skilled", 1400.00),
        ("Sunil Dutt", "sunil@example.com", "9876543216", "Carpenter", "Skilled", 1000.00),
        ("Anil Gupta", "anil@example.com", "9876543217", "Painter", "Semi-Skilled", 750.00),
        ("Ramesh Lal", "ramesh@example.com", "9876543218", "Laborer", "Unskilled", 500.00),
        ("Mahesh Chand", "mahesh@example.com", "9876543219", "Laborer", "Unskilled", 500.00)
    ]
    
    workers = []
    for name, email, phone, role, w_type, wage in workers_data:
        w = Worker(
            full_name=name,
            email=email,
            phone=phone,
            role_title=role,
            worker_type=w_type,
            wage_rate=Decimal(str(wage)),
            active=True
        )
        db.add(w)
        workers.append(w)
    db.commit()
    
    # Add skills
    for w in workers:
        skill1 = WorkerSkill(worker_id=w.id, skill_name=w.role_title, proficiency_level="Expert" if w.worker_type=="Skilled" else "Intermediate")
        db.add(skill1)
    db.commit()
    
    print("Scheduling worker shifts & calendars...")
    # Project 1 Schedules
    schedules = []
    for idx, w in enumerate(workers[:7]):
        shift = "Night" if idx % 3 == 0 else "Day"
        sched = WorkerSchedule(
            worker_id=w.id,
            project_id=proj1.id,
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=30),
            shift_type=shift
        )
        db.add(sched)
        schedules.append(sched)
        
    # Project 3 Schedules
    for idx, w in enumerate(workers[5:]):
        sched = WorkerSchedule(
            worker_id=w.id,
            project_id=proj3.id,
            start_date=today - timedelta(days=20),
            end_date=today + timedelta(days=20),
            shift_type="Day"
        )
        db.add(sched)
        schedules.append(sched)
    db.commit()
    
    print("Seeding attendance records...")
    # Attendance logs for the last 5 days
    for d_idx in range(5):
        att_date = today - timedelta(days=d_idx)
        for w in workers[:8]:
            status = "Present"
            hours = Decimal("8.0")
            overtime = Decimal("0.0")
            
            # Add some variability
            if w.id % 4 == 0 and d_idx == 1:
                status = "Late"
                hours = Decimal("7.0")
                overtime = Decimal("1.0")
            elif w.id % 7 == 0 and d_idx == 3:
                status = "Absent"
                hours = Decimal("0.0")
                
            att = Attendance(
                worker_id=w.id,
                date=att_date,
                status=status,
                hours_worked=hours,
                overtime_hours=overtime
            )
            db.add(att)
    db.commit()
    
    print("Seeding leave requests...")
    l1 = LeaveRequest(worker_id=workers[1].id, start_date=today + timedelta(days=5), end_date=today + timedelta(days=7), leave_type="Casual", status="Pending", reason="Family emergency")
    l2 = LeaveRequest(worker_id=workers[3].id, start_date=today - timedelta(days=10), end_date=today - timedelta(days=8), leave_type="Sick", status="Approved", reason="High fever recovery")
    db.add_all([l1, l2])
    db.commit()
    
    print("Configuring itemized budgets...")
    # Project 1 Budget
    b1 = Budget(
        project_id=proj1.id,
        estimated_cost=Decimal("45000000.00"),
        optimized_cost=Decimal("42500000.00"),
        currency="INR",
        ai_summary="The initial construction estimate was calculated at INR 45,000,000. Materials represent 62.5% of total budget costs.",
        ai_recommendations="- Material Savings: Buy cement in bulk to save up to 8%.\n- Labor Optimization: Reduce general helpers during concrete curing."
    )
    # Project 3 Budget
    b3 = Budget(
        project_id=proj3.id,
        estimated_cost=Decimal("17500000.00"),
        optimized_cost=Decimal("16900000.00"),
        currency="INR",
        ai_summary="Substation project contains heavy equipment rental costs representing 35.2% of the budget.",
        ai_recommendations="- Equipment Efficiency: Share excavators across zones to reduce idle rental fees."
    )
    db.add_all([b1, b3])
    db.commit()
    db.refresh(b1)
    db.refresh(b3)
    
    # Budget Items
    items_b1 = [
        BudgetItem(budget_id=b1.id, category="Material", description="Portland Pozzolana Cement", quantity=Decimal("5000"), unit_price=Decimal("400"), total_price=Decimal("2000000")),
        BudgetItem(budget_id=b1.id, category="Material", description="Structural Steel Rebars", quantity=Decimal("150"), unit_price=Decimal("45000"), total_price=Decimal("6750000")),
        BudgetItem(budget_id=b1.id, category="Labor", description="Masons & Helpers Daily Wages", quantity=Decimal("1200"), unit_price=Decimal("800"), total_price=Decimal("960000")),
        BudgetItem(budget_id=b1.id, category="Equipment", description="Crawler Excavator Rental", quantity=Decimal("45"), unit_price=Decimal("12000"), total_price=Decimal("540000")),
        BudgetItem(budget_id=b1.id, category="Indirect", description="Indirect site operational costs (10% overhead)", quantity=Decimal("1"), unit_price=Decimal("1000000"), total_price=Decimal("1000000")),
        BudgetItem(budget_id=b1.id, category="Contingency", description="Emergency contingency buffer (5% allocation)", quantity=Decimal("1"), unit_price=Decimal("500000"), total_price=Decimal("500000"))
    ]
    
    items_b3 = [
        BudgetItem(budget_id=b3.id, category="Equipment", description="Heavy Duty Transformers", quantity=Decimal("2"), unit_price=Decimal("3500000"), total_price=Decimal("7000000")),
        BudgetItem(budget_id=b3.id, category="Labor", description="Electrical Subcontracting Crew", quantity=Decimal("30"), unit_price=Decimal("25000"), total_price=Decimal("750000"))
    ]
    db.add_all(items_b1 + items_b3)
    
    # Labor & Equipment cost summaries
    lc1 = LaborCost(project_id=proj1.id, worker_type="Mason", worker_count=3, daily_rate=Decimal("1000.00"), days=45, total_cost=Decimal("135000.00"))
    lc2 = LaborCost(project_id=proj1.id, worker_type="Electrician", worker_count=1, daily_rate=Decimal("1200.00"), days=20, total_cost=Decimal("24000.00"))
    eq1 = EquipmentCost(project_id=proj1.id, equipment_name="Crawler Excavator", days_used=25, daily_rate=Decimal("12000.00"), total_cost=Decimal("300000.00"))
    eq2 = EquipmentCost(project_id=proj3.id, equipment_name="Mobile Crane 50T", days_used=15, daily_rate=Decimal("18000.00"), total_cost=Decimal("270000.00"))
    db.add_all([lc1, lc2, eq1, eq2])
    db.commit()
    
    print("Writing inventory and material registries...")
    mat1 = Material(project_id=proj1.id, material_name="Portland Pozzolana Cement", category="Cement", quantity=Decimal("3000.00"), unit="Bags", unit_price=Decimal("400.00"), total_cost=Decimal("1200000.00"))
    mat2 = Material(project_id=proj1.id, material_name="Structural Steel Rebars", category="Steel", quantity=Decimal("80.00"), unit="Tons", unit_price=Decimal("45000.00"), total_cost=Decimal("3600000.00"))
    mat3 = Material(project_id=proj3.id, material_name="CPVC Pipes 3 inch", category="Plumbing", quantity=Decimal("500.00"), unit="Meters", unit_price=Decimal("250.00"), total_cost=Decimal("125000.00"))
    db.add_all([mat1, mat2, mat3])
    
    inv1 = Inventory(material_name="Portland Pozzolana Cement", quantity_available=Decimal("4500.00"), quantity_reserved=Decimal("2500.00"), unit="Bags", warehouse_capacity=Decimal("10000.00"))
    inv2 = Inventory(material_name="Structural Steel Rebars", quantity_available=Decimal("60.00"), quantity_reserved=Decimal("50.00"), unit="Tons", warehouse_capacity=Decimal("200.00"))  # represents shortage!
    inv3 = Inventory(material_name="CPVC Pipes 3 inch", quantity_available=Decimal("1200.00"), quantity_reserved=Decimal("300.00"), unit="Meters", warehouse_capacity=Decimal("5000.00"))
    db.add_all([inv1, inv2, inv3])
    db.commit()
    
    print("Creating suppliers and purchase orders...")
    sup1 = Supplier(supplier_name="UltraTech Cement Depot", rating=Decimal("4.50"), contact_info="sales@ultratech.com", address="MIDC Area, Mumbai", active=True)
    sup2 = Supplier(supplier_name="Tata Steel Distributors", rating=Decimal("4.85"), contact_info="orders@tatasteel.com", address="Jamshedpur, JH", active=True)
    db.add_all([sup1, sup2])
    db.commit()
    db.refresh(sup1)
    db.refresh(sup2)
    
    po1 = PurchaseOrder(project_id=proj1.id, supplier_id=sup1.id, material_name="Portland Pozzolana Cement", quantity=Decimal("1000.00"), unit_price=Decimal("380.00"), total_cost=Decimal("380000.00"), status="Pending")
    po2 = PurchaseOrder(project_id=proj1.id, supplier_id=sup2.id, material_name="Structural Steel Rebars", quantity=Decimal("40.00"), unit_price=Decimal("43000.00"), total_cost=Decimal("1720000.00"), status="Delivered")
    db.add_all([po1, po2])
    db.commit()
    
    print("Generating risk scores, weather cache, and predictions...")
    r1 = Risk(
        project_id=proj1.id,
        risk_score=45,
        delay_probability=Decimal("28.50"),
        executive_summary="Moderate risk. Steel supply chain bottlenecks have created a delay projection. Weather conditions are standard.",
        weather_risk_severity="Low",
        material_risk_severity="High",
        budget_risk_severity="Low",
        worker_risk_severity="Low",
        equipment_risk_severity="Medium",
        supplier_risk_severity="Low",
        safety_risk_severity="Low",
        timeline_risk_severity="Medium",
        ai_mitigation_suggestions="- Expedite Tata Steel purchase order.\n- Allocate crane tasks to day-shifts to lower risk."
    )
    
    r3 = Risk(
        project_id=proj3.id,
        risk_score=75,
        delay_probability=Decimal("68.00"),
        executive_summary="Critical delay risks. Electrical component shipping is delayed by 14 days. Monsoons are impacting site installation schedules.",
        weather_risk_severity="High",
        material_risk_severity="Critical",
        budget_risk_severity="Medium",
        worker_risk_severity="Medium",
        equipment_risk_severity="Low",
        supplier_risk_severity="High",
        safety_risk_severity="Low",
        timeline_risk_severity="High",
        ai_mitigation_suggestions="- Deploy waterproof shields to continue cable layouts.\n- Renegotiate grid connection delay clauses."
    )
    db.add_all([r1, r3])
    
    hist1 = RiskHistory(project_id=proj1.id, risk_score=42, delay_probability=Decimal("25.00"), executive_summary="Initial operational risk review", created_at=datetime.now() - timedelta(days=7))
    hist2 = RiskHistory(project_id=proj1.id, risk_score=45, delay_probability=Decimal("28.50"), executive_summary="Updated with steel shortage status", created_at=datetime.now())
    db.add_all([hist1, hist2])
    
    w1 = WeatherData(project_id=proj1.id, location="Mumbai, IN", temperature=Decimal("31.50"), wind_speed=Decimal("12.40"), precipitation=Decimal("0.00"), humidity=Decimal("78.00"), weather_description="Scattered Clouds", alerts="", cached_at=datetime.now())
    w3 = WeatherData(project_id=proj3.id, location="Delhi, IN", temperature=Decimal("38.00"), wind_speed=Decimal("22.00"), precipitation=Decimal("5.00"), humidity=Decimal("52.00"), weather_description="Thundershowers", alerts="High Winds Alert", cached_at=datetime.now())
    db.add_all([w1, w3])
    
    pred1 = DelayPrediction(project_id=proj1.id, probability=Decimal("28.50"), predicted_delay_days=12, variance_days=5, root_causes="Steel shipment delays.", recovery_recommendations="Add night shifts for structural columns.", updated_at=datetime.now())
    pred3 = DelayPrediction(project_id=proj3.id, probability=Decimal("68.00"), predicted_delay_days=25, variance_days=18, root_causes="Heavy rain combined with supplier delay.", recovery_recommendations="Adjust milestone dates.", updated_at=datetime.now())
    db.add_all([pred1, pred3])
    db.commit()
    
    print("Writing project milestones...")
    # Project 1 Milestones
    m1 = Milestone(project_id=proj1.id, milestone_name="Excavation & Shoring", description="Site excavation to basement level.", planned_end_date=today - timedelta(days=60), actual_end_date=today - timedelta(days=58), completion_percentage=Decimal("100.00"), status="Completed")
    m2 = Milestone(project_id=proj1.id, milestone_name="Foundation Concrete", description="Pouring of core raft foundation.", planned_end_date=today - timedelta(days=20), actual_end_date=today - timedelta(days=18), completion_percentage=Decimal("100.00"), status="Completed")
    m3 = Milestone(project_id=proj1.id, milestone_name="Structural Framing (L1-L5)", description="Columns and slab pouring for levels 1 to 5.", planned_end_date=today + timedelta(days=30), completion_percentage=Decimal("45.00"), status="On-Time")
    m4 = Milestone(project_id=proj1.id, milestone_name="Facade Installation", description="Exterior glass cladding.", planned_end_date=today + timedelta(days=120), completion_percentage=Decimal("0.00"), status="Planning")
    
    # Project 3 Milestones (Delayed)
    m3_1 = Milestone(project_id=proj3.id, milestone_name="Civil Foundations", description="Transformer bays civil works.", planned_end_date=today - timedelta(days=60), actual_end_date=today - timedelta(days=55), completion_percentage=Decimal("100.00"), status="Completed")
    m3_2 = Milestone(project_id=proj3.id, milestone_name="Cable Trenching", description="Laying grid connection trenches.", planned_end_date=today - timedelta(days=15), completion_percentage=Decimal("80.00"), status="Delayed")  # Planned end date is in the past!
    m3_3 = Milestone(project_id=proj3.id, milestone_name="Transformer Assembly", description="Heavy transformer rigging.", planned_end_date=today + timedelta(days=10), completion_percentage=Decimal("10.00"), status="At-Risk")
    
    db.add_all([m1, m2, m3, m4, m3_1, m3_2, m3_3])
    db.commit()
    
    print("Writing progress reports...")
    pr1 = ProgressReport(
        project_id=proj1.id,
        report_type="Weekly",
        start_date=today - timedelta(days=7),
        end_date=today,
        overall_completion_percentage=Decimal("48.50"),
        milestones_completed_count=2,
        budget_spent_so_far=Decimal("12500000.00"),
        resource_utilization_rate=Decimal("92.00"),
        variance_status="On-Track",
        ai_summary="Project is progressing steadily. Concrete works are complete. Framing is active on L3.",
        created_by=engineer.id
    )
    db.add(pr1)
    
    dlog1 = DailyLog(project_id=proj1.id, log_date=today, update_text="Poured concrete for L3 elevator core. Delivered steel reinforcement bundles.", submitted_by=engineer.id)
    db.add(dlog1)
    db.commit()
    
    print("Generating visual site image audits and safety records...")
    # Add Site Images
    img1 = SiteImage(project_id=proj1.id, image_path="/uploads/images/site_view_1.jpg", capture_date=today - timedelta(days=2))
    img2 = SiteImage(project_id=proj1.id, image_path="/uploads/images/site_view_2.jpg", capture_date=today)
    db.add_all([img1, img2])
    db.commit()
    db.refresh(img1)
    db.refresh(img2)
    
    # Image analysis audits (PPE detections & Safety compliance)
    an1 = SiteImageAnalysis(
        project_id=proj1.id,
        site_image_id=img1.id,
        progress_percentage=Decimal("45.00"),
        construction_stage="Wall Framing",
        safety_issues=json.dumps(["No Safety Harness on scaffold worker at Zone B"]),
        recommendations="Deploy supervisor to Zone B to enforce safety harness compliance immediately.",
        annotated_image_path="/uploads/annotated/site_view_1_annotated.jpg"
    )
    
    an2 = SiteImageAnalysis(
        project_id=proj1.id,
        site_image_id=img2.id,
        progress_percentage=Decimal("48.00"),
        construction_stage="Slab Pouring",
        safety_issues=json.dumps([]),  # Fully compliant!
        recommendations="General site keeping is optimal. Continue current site protocols.",
        annotated_image_path="/uploads/annotated/site_view_2_annotated.jpg"
    )
    db.add_all([an1, an2])
    db.commit()
    
    print("Generating suppliers invoices & comparisons...")
    inv_rec1 = Invoice(
        project_id=proj1.id,
        invoice_number="INV-2026-9081",
        invoice_date=today - timedelta(days=10),
        vendor_name="UltraTech Cement Depot",
        vendor_gst="27ULTRA1234A1Z5",
        total_amount=Decimal("145000.00"),
        tax_amount=Decimal("26100.00"),
        status="Completed",
        confidence_score=Decimal("92.50"),
        ocr_raw_text="Vendor: UltraTech Cement Depot\nInvoice No: INV-2026-9081\nDate: 2026-10-05\nGST: 27ULTRA1234A1Z5\nTotal: 145000.00\nSGST/CGST: 26100.00\nCement Bag OPC 53 Grade - 300 Bags - Price 400.00 - Total 120000.00"
    )
    
    inv_rec2 = Invoice(
        project_id=proj1.id,
        invoice_number="INV-2026-9122",
        invoice_date=today,
        vendor_name="Tata Steel Distributors",
        vendor_gst="27TATA8827B1Z3",
        total_amount=Decimal("380000.00"),
        tax_amount=Decimal("68400.00"),
        status="Pending",
        confidence_score=Decimal("95.00"),
        ocr_raw_text="Vendor: Tata Steel Distributors\nInvoice No: INV-2026-9122\nDate: 2026-10-15\nGST: 27TATA8827B1Z3\nTotal: 380000.00\nSteel Rebars 12mm - 8 Tons - Price 45000.00 - Total 360000.00"
    )
    db.add_all([inv_rec1, inv_rec2])
    db.commit()
    db.refresh(inv_rec1)
    db.refresh(inv_rec2)
    
    # Invoice Items
    item1 = InvoiceItem(invoice_id=inv_rec1.id, description="Portland Pozzolana Cement", quantity=Decimal("300.00"), unit_price=Decimal("400.00"), total_price=Decimal("120000.00"), material_id=mat1.id)
    item2 = InvoiceItem(invoice_id=inv_rec2.id, description="Structural Steel Rebars", quantity=Decimal("8.00"), unit_price=Decimal("45000.00"), total_price=Decimal("360000.00"), material_id=mat2.id)
    db.add_all([item1, item2])
    db.commit()
    db.refresh(item1)
    db.refresh(item2)
    
    # Invoice Comparisons
    comp_1 = InvoiceComparison(invoice_id=inv_rec1.id, project_id=proj1.id, item_id=item1.id, budgeted_amount=Decimal("120000.00"), actual_amount=Decimal("120000.00"), variance=Decimal("0.00"), analysis_notes="Perfect match against budgeted materials price.")
    comp_2 = InvoiceComparison(invoice_id=inv_rec2.id, project_id=proj1.id, item_id=item2.id, budgeted_amount=Decimal("360000.00"), actual_amount=Decimal("360000.00"), variance=Decimal("0.00"), analysis_notes="Perfect match against steel budget allocation.")
    db.add_all([comp_1, comp_2])
    
    # Voice command log & notifications
    vlog1 = VoiceCommandLog(user_id=engineer.id, project_id=proj1.id, command_text="get progress overview", response_text="The project 'Apex Commercial Tower' is at 48.5% overall completion percentage, with 2 milestones completed and no active delays.", audio_path="")
    vlog2 = VoiceCommandLog(user_id=engineer.id, project_id=proj1.id, command_text="show safety alerts", response_text="There is 1 active safety hazard: 'No Safety Harness on scaffold worker at Zone B'.", audio_path="")
    db.add_all([vlog1, vlog2])
    db.commit()
    
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
