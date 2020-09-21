#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the image_retrieval module.
"""
import pytest

from image_retrieval import image_retrieval


def test_something():
    assert True


def test_with_error():
    with pytest.raises(ValueError):
        # Do something that raises a ValueError
        raise(ValueError)


# Fixture example
@pytest.fixture
def an_object():
    return {}


def test_image_retrieval(an_object):
    assert an_object == {}
