from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.project import Project, ProjectStatus, ProjectMember, Document, Drawing, SiteImage
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.core.files import delete_physical_file

class ProjectService:
    @staticmethod
    def create_project(db: Session, project_in: ProjectCreate, creator_id: int) -> Project:
        """
        Creates a new project. Checks if a project with the same name already exists for the client.
        Automatically registers the project creator as an Admin member of the project.
        """
        # Check client duplicate name constraint
        existing = db.query(Project).filter(
            Project.project_name == project_in.project_name,
            Project.client_name == project_in.client_name
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A project with this name already exists for the specified client."
            )

        project = Project(
            project_name=project_in.project_name,
            description=project_in.description,
            client_name=project_in.client_name,
            location=project_in.location,
            start_date=project_in.start_date,
            expected_end_date=project_in.expected_end_date,
            status=project_in.status,
            budget=project_in.budget,
            created_by=creator_id
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # Auto-assign creator as Project Member with Admin role
        member = ProjectMember(
            project_id=project.id,
            user_id=creator_id,
            role=UserRole.ADMIN
        )
        db.add(member)
        db.commit()
        
        return project

    @staticmethod
    def get_projects(
        db: Session,
        current_user: User,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        status_filter: Optional[ProjectStatus] = None
    ) -> Tuple[int, List[Project]]:
        """
        Queries all projects visible to the current user.
        - Admin can see all projects.
        - PM and Site Engineer can only see projects they are assigned to.
        Supports search filters (project_name, client_name, location) and status filters.
        """
        query = db.query(Project)

        # Enforce scope visibility rules
        if current_user.role != UserRole.ADMIN:
            query = query.join(ProjectMember).filter(ProjectMember.user_id == current_user.id)

        # Apply search string if any
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Project.project_name.ilike(search_pattern),
                    Project.client_name.ilike(search_pattern),
                    Project.location.ilike(search_pattern)
                )
            )

        # Apply status filter if any
        if status_filter:
            query = query.filter(Project.status == status_filter)

        total = query.count()
        
        # Paginate results
        offset = (page - 1) * size
        items = query.order_by(Project.created_at.desc()).offset(offset).limit(size).all()

        return total, items

    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """Fetches detailed project record by ID."""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def update_project(db: Session, project: Project, project_in: ProjectUpdate) -> Project:
        """
        Updates metadata fields on an existing project.
        Re-verifies name/client duplicates if changed.
        """
        update_data = project_in.model_dump(exclude_unset=True)
        
        # Check if project name or client name changes would cause duplicates
        new_name = update_data.get("project_name", project.project_name)
        new_client = update_data.get("client_name", project.client_name)
        if new_name != project.project_name or new_client != project.client_name:
            existing = db.query(Project).filter(
                Project.project_name == new_name,
                Project.client_name == new_client,
                Project.id != project.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A project with this name already exists for the specified client."
                )

        for field, value in update_data.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project: Project):
        """
        Deletes project and physically removes all associated drawings, documents, and images.
        """
        # Collect physical files to delete them from storage post DB transaction
        files_to_delete = []
        for doc in project.documents:
            files_to_delete.append(doc.file_path)
        for drawing in project.drawings:
            files_to_delete.append(drawing.drawing_path)
        for img in project.images:
            files_to_delete.append(img.image_path)

        db.delete(project)
        db.commit()

        # Clean up disk files
        for path in files_to_delete:
            delete_physical_file(path)

    # Project Members Management
    @staticmethod
    def add_member(db: Session, project_id: int, user_id: int, role: UserRole) -> ProjectMember:
        """Registers a user to a project with a specific role."""
        # Ensure user exists
        user_exists = db.query(User).filter(User.id == user_id).first()
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found.")

        # Ensure not already a member
        existing = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        if existing:
            # Update role instead of duplicating
            existing.role = role
            db.commit()
            db.refresh(existing)
            return existing

        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove_member(db: Session, project_id: int, user_id: int):
        """Removes a user from a project membership."""
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        if not member:
            raise HTTPException(status_code=404, detail="Project member not found.")
        db.delete(member)
        db.commit()

    # Uploads Database Bindings
    @staticmethod
    def add_document(db: Session, project_id: int, file_name: str, file_type: str, file_path: str, user_id: int) -> Document:
        doc = Document(
            project_id=project_id,
            file_name=file_name,
            file_type=file_type,
            file_path=file_path,
            uploaded_by=user_id
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def add_drawing(db: Session, project_id: int, drawing_name: str, drawing_path: str, user_id: int) -> Drawing:
        drawing = Drawing(
            project_id=project_id,
            drawing_name=drawing_name,
            drawing_path=drawing_path,
            uploaded_by=user_id
        )
        db.add(drawing)
        db.commit()
        db.refresh(drawing)
        return drawing

    @staticmethod
    def add_site_image(db: Session, project_id: int, image_path: str, capture_date: date, user_id: int) -> SiteImage:
        img = SiteImage(
            project_id=project_id,
            image_path=image_path,
            capture_date=capture_date,
            uploaded_by=user_id
        )
        db.add(img)
        db.commit()
        db.refresh(img)
        return img

    @staticmethod
    def get_document(db: Session, document_id: int) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id).first()

    @staticmethod
    def delete_file_record(db: Session, file_id: int, file_category: str):
        """
        Deletes drawing, document, or image database records and sweeps physical files.
        """
        if file_category == "document":
            record = db.query(Document).filter(Document.id == file_id).first()
            if not record:
                raise HTTPException(status_code=404, detail="Document record not found")
            path = record.file_path
        elif file_category == "drawing":
            record = db.query(Drawing).filter(Drawing.id == file_id).first()
            if not record:
                raise HTTPException(status_code=404, detail="Drawing record not found")
            path = record.drawing_path
        elif file_category == "image":
            record = db.query(SiteImage).filter(SiteImage.id == file_id).first()
            if not record:
                raise HTTPException(status_code=404, detail="Image record not found")
            path = record.image_path
        else:
            raise HTTPException(status_code=400, detail="Invalid file category")

        db.delete(record)
        db.commit()
        delete_physical_file(path)
