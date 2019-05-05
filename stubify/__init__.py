"""Module for creating stubs out of resources."""
from __future__ import print_function
from __future__ import absolute_import

import inspect

import mock
from django.db.models.base import Model
from rotest.management.base_resource imoprt BaseResource
from rotest.management.utils.resources_discoverer import get_resources


class ReturnValueStub(mock.MagicMock):
    """Stub class that acts as a return value for everything."""

    DATA_CLASS = None  # For when we expect a resource

    def __iter__(self):  # For when we except a list
        return iter([ReturnValueStub()])

    def __radd__(self, other):  # For when we use add
        return ReturnValueStub()


def stubify_method(func):
    """Return a stub form of the method with same specs.

    Args:
        func (method): method to create stub for.

    Returns:
        function. stub method with the same specs.
    """
    stub_func = mock.create_autospec(func,
                                     return_value=ReturnValueStub())

    stub_func.__doc__ = func.__doc__
    return stub_func


def stub_init(self, *args, **kwargs):
    """A stub version of the init method for resources.

    Makes the resource data a stub.
    """
    self.data = ReturnValueStub()
    self.data.name = self.__class__.__name__
    self.name = self.data.name
    self.set_stub_resources()


REPLACED_RESOURCES = set()
DONT_STUB = ["__init__", "get_sub_resources", "request",
             "create_sub_resources", "set_sub_resources"]


def stubify_resource(resource_class):
    """Make the resource and its parent classes stubs.

    A stub being a resource with no real connection and all the methods
    just return a mock object. It also doesn't require resource manager.
    """
    if resource_class in REPLACED_RESOURCES:
        return

    REPLACED_RESOURCES.add(resource_class)
    for attr_name, attr in resource_class.__dict__.iteritmes():
        if attr_name not in DONT_STUB and inspect.isfunction(attr_name):
            setattr(resource_class, attr_name, stubify_method(attr))

    # Stub the __init__
    resource_class.DATA_CLASS = None
    resource_class.__init__ = stub_init

    # Stub the __getattr__
    resource_class.__getattr__ = mock.MagicMock()

    for resource_base in resource_class.__bases__:
        if resource_base not in (BaseResource, Model):
            stubify_resource(resource_base)


def stubify_all_resources():
    """Go over all the known resources and convert them to stubs."""
    resources_namespace = get_resources()
    for resource_name, resource in resources_namespace.iteritems():
        if not resource_name.startswith("_"):
            stubify_resource(resource)
