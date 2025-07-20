from robusta.integrations.slack import SlackSender


def test_title_without_mentions():
    title = "Title with no mentions"
    new_title, mention = SlackSender.extract_mentions(title)
    assert new_title == title
    assert mention == ""

def test_title_with_single_mention():
    title = "Title with single mention <@U024BE7LH>"
    new_title, mention = SlackSender.extract_mentions(title)
    assert new_title == "Title with single mention"
    assert mention == " <@U024BE7LH>"

def test_title_with_two_mentions():
    title = "Title with <@U024BE7LG> two mentions <@U024BE7LH>"
    new_title, mention = SlackSender.extract_mentions(title)
    assert new_title == "Title with  two mentions"
    assert mention == " <@U024BE7LG> <@U024BE7LH>"
