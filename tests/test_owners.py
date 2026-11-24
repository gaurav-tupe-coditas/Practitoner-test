from actiontrack.owners import AMBIGUOUS, RESOLVED, UNASSIGNED, Owner, resolve_owner

TWO_PRIYAS = ["Priya Nair", "Priya Shah", "Sam Okafor"]
REGISTRY = {"Priya Nair", "Priya Shah", "Rahul Mehta", "Rahul Verma", "Sam Okafor", "Anita Desai"}


def test_forms():  # T-11
    assert resolve_owner("Priya N.", TWO_PRIYAS, REGISTRY) == [Owner("Priya Nair", RESOLVED)]
    assert resolve_owner("@anita", ["Anita Desai"], REGISTRY) == [Owner("Anita Desai", RESOLVED)]
    assert resolve_owner("Anita & Rahul", ["Anita Desai", "Rahul Mehta"], REGISTRY) == [
        Owner("Anita Desai", RESOLVED), Owner("Rahul Mehta", RESOLVED)]
    assert resolve_owner("Lena (with Priya)", ["Lena Fischer", "Priya Nair"], REGISTRY) == [Owner("Lena Fischer", RESOLVED)]


def test_resolution():  # T-12
    assert resolve_owner("Priya", TWO_PRIYAS, REGISTRY) == [Owner("Priya", AMBIGUOUS)]
    assert resolve_owner("Rahul", [], REGISTRY) == [Owner("Rahul", AMBIGUOUS)]       # no attendees, two known
    assert resolve_owner("Sam", [], REGISTRY) == [Owner("Sam Okafor", RESOLVED)]     # no attendees, one known
    assert resolve_owner("Priya", ["Priya Shah", "Anita Desai"], REGISTRY) == [Owner("Priya Shah", RESOLVED)]


def test_group_owners():  # T-13
    nine = [f"P{i} Q" for i in range(9)]
    assert len(resolve_owner("Everyone", nine, REGISTRY)) == 9
    assert [o.name for o in resolve_owner("Team", ["A B", "C D"], REGISTRY)] == ["A B", "C D"]
    assert resolve_owner("TBD", nine, REGISTRY) == [Owner(None, UNASSIGNED)]
    assert resolve_owner("Someone", nine, REGISTRY) == [Owner(None, UNASSIGNED)]
    assert resolve_owner("Everyone", [], REGISTRY) == [Owner(None, UNASSIGNED)]
    assert resolve_owner(None, nine, REGISTRY) == [Owner(None, UNASSIGNED)]
