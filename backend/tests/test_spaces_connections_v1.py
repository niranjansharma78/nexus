from app.services.spaces_service import ensure_spaces_schema,list_spaces,list_mailboxes_with_spaces
def test_default_spaces():
    ensure_spaces_schema()
    names={x["name"] for x in list_spaces()}
    assert {"Personal","Family","Claron","Congen","Tekhelsoft"}.issubset(names)
def test_mailboxes_list():
    assert isinstance(list_mailboxes_with_spaces(),list)
