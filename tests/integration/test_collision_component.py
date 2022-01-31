import pytest

import gamelib
from gamelib import ecs
from gamelib import geometry


@pytest.fixture(autouse=True)
def cleanup():
    ecs.Entity.clear()


class Entity1(ecs.Entity):
    collider: ecs.Collider


class Entity2(ecs.Entity):
    collider: ecs.Collider


class Entity3(ecs.Entity):
    collider: ecs.Collider
    transform: ecs.Transform


def test_first_entity_hit_base_case():
    model1 = geometry.GridMesh(4, 4)
    model2 = geometry.GridMesh(4, 4)
    model2.vertices += gamelib.Vec3(0, 0, 1)
    entity1 = Entity1(ecs.Collider.from_model(model1))
    entity2 = Entity2(ecs.Collider.from_model(model2))

    ray_top = geometry.Ray((2, 2, 10), (0, 0, -1))
    ray_bottom = geometry.Ray((2, 2, -10), (0, 0, 1))
    ray_miss = geometry.Ray((2, 2, 10), (1, 1, -1))

    assert ecs.collisions.first_entity_hit(ray_top).id == entity2.id
    assert ecs.collisions.first_entity_hit(ray_bottom).id == entity1.id
    assert ecs.collisions.first_entity_hit(ray_miss) is None


def test_first_entity_hit_with_transform():
    model1 = geometry.GridMesh(4, 4)
    model1.vertices += gamelib.Vec3(0, 0, 1)
    model3 = geometry.GridMesh(4, 4)
    transform = ecs.Transform.create(pos=(0, 0, 3), theta=30)
    entity1 = Entity1(ecs.Collider.from_model(model1))
    entity3 = Entity3(ecs.Collider.from_model(model3), transform)

    ray_top = geometry.Ray((2, 2, 10), (0, 0, -1))
    ray_bottom = geometry.Ray((2, 2, -10), (0, 0, 1))
    ray_miss = geometry.Ray((2, 2, 10), (1, 1, -1))

    assert ecs.collisions.first_entity_hit(ray_top).id == entity3.id
    assert ecs.collisions.first_entity_hit(ray_bottom).id == entity1.id
    assert ecs.collisions.first_entity_hit(ray_miss) is None
