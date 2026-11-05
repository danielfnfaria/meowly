from purr_core.models import Component, Environment, Owner, Template
from purr_core.repositories.base import Repository


class OwnerRepository(Repository[Owner]):
    model = Owner


class ComponentRepository(Repository[Component]):
    model = Component


class TemplateRepository(Repository[Template]):
    model = Template


class EnvironmentRepository(Repository[Environment]):
    model = Environment
