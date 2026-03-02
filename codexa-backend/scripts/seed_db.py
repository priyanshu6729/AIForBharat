from libs.common.db import SessionLocal
from libs.common.models import Tenant, User, Project


def main():
    session = SessionLocal()
    tenant = session.query(Tenant).filter(Tenant.name == "prototype").first()
    if tenant is None:
        tenant = Tenant(name="prototype", plan="prototype")
        session.add(tenant)
        session.commit()
        session.refresh(tenant)

    user = session.query(User).filter(User.email == "dev@codexa.local").first()
    if user is None:
        user = User(tenant_id=tenant.id, email="dev@codexa.local", role="admin")
        session.add(user)
        session.commit()
        session.refresh(user)

    project = session.query(Project).filter(Project.name == "sample-project").first()
    if project is None:
        project = Project(tenant_id=tenant.id, name="sample-project", default_language="python")
        session.add(project)
        session.commit()
        session.refresh(project)

    print("tenant_id=", tenant.id)
    print("user_id=", user.id)
    print("project_id=", project.id)


if __name__ == "__main__":
    main()
