"""
Robot-Q Person and Relationship Tool

This module owns deterministic information about people and their
relationships to one another.

The language model should not guess these relationships. Other parts
of Robot-Q can query this module when they need authoritative
information about who someone is or how two people are related.
"""


# ============================================================
# PEOPLE
# ============================================================

# Each person has a stable internal ID.
#
# The ID is what Robot-Q uses internally.
# The display name is what Robot-Q can show to humans.

PEOPLE = {
    "camille": {
        "name": "Camille",
        "type": "human",
    },

    "shelby": {
        "name": "Shelby",
        "type": "human",
    },

    "robot_q": {
        "name": "Robot-Q",
        "type": "robot",
    },
}


# ============================================================
# RELATIONSHIPS
# ============================================================

# Relationships are directional:
#
#     subject -> relationship -> object
#
# Example:
#
#     Camille -> girlfriend_of -> Shelby
#
# Direction is stored explicitly so the AI does not have to infer
# who the relationship belongs to.

RELATIONSHIPS = {
    ("camille", "shelby"): "girlfriend_of",
    ("shelby", "camille"): "girlfriend_of",

    ("camille", "robot_q"): "companion_of",
    ("robot_q", "camille"): "companion_of",
}


# ============================================================
# RELATIONSHIP LANGUAGE
# ============================================================

# Internal relationship names stay machine-friendly.
#
# This dictionary converts them into language that can be given
# to the AI or displayed directly.

RELATIONSHIP_TEXT = {
    "girlfriend_of": "girlfriend",
    "companion_of": "companion",
}


# ============================================================
# PERSON LOOKUP
# ============================================================

def get_person(person_id):
    """
    Return information about one person.

    Example:
        get_person("camille")
    """

    return PEOPLE.get(person_id)


def get_person_name(person_id):
    """
    Return only the person's display name.

    Example:
        get_person_name("camille")
        -> "Camille"
    """

    person = get_person(person_id)

    if person is None:
        return None

    return person["name"]


# ============================================================
# RELATIONSHIP LOOKUP
# ============================================================

def get_relationship(subject_id, object_id):
    """
    Return the relationship from one person to another.

    Direction matters.

    Example:
        get_relationship("camille", "shelby")
        -> "girlfriend_of"
    """

    return RELATIONSHIPS.get(
        (subject_id, object_id)
    )


def get_relationship_text(subject_id, object_id):
    """
    Return a human-readable relationship.

    Example:
        get_relationship_text("camille", "shelby")
        -> "girlfriend"
    """

    relationship = get_relationship(
        subject_id,
        object_id
    )

    if relationship is None:
        return None

    return RELATIONSHIP_TEXT.get(
        relationship,
        relationship
    )


# ============================================================
# RELATIONSHIP FACT
# ============================================================

def get_relationship_fact(subject_id, object_id):
    """
    Return a complete factual statement describing the
    relationship.

    This is useful when supplying relationship information
    to the language model.

    Example:
        get_relationship_fact("camille", "shelby")

        -> "Camille is Shelby's girlfriend."
    """

    subject_name = get_person_name(subject_id)
    object_name = get_person_name(object_id)

    relationship = get_relationship_text(
        subject_id,
        object_id
    )

    if (
        subject_name is None
        or object_name is None
        or relationship is None
    ):
        return None

    return (
        f"{subject_name} is "
        f"{object_name}'s {relationship}."
    )


# ============================================================
# ALL RELATIONSHIPS FOR A PERSON
# ============================================================

def get_relationships_for(person_id):
    """
    Return every known relationship involving a person.

    Example:
        get_relationships_for("camille")
    """

    results = []

    for (
        subject_id,
        object_id
    ), relationship in RELATIONSHIPS.items():

        if (
            subject_id == person_id
            or object_id == person_id
        ):

            results.append({
                "subject": subject_id,
                "relationship": relationship,
                "object": object_id,
            })

    return results


# ============================================================
# CURRENT SPEAKER CONTEXT
# ============================================================

def get_speaker_context(speaker_id):
    """
    Return deterministic identity information for the
    current speaker.

    This allows the controller to tell the AI exactly who
    words such as "I", "me", "my", "you", and "your" refer to.

    For now, "you" always refers to Robot-Q because Robot-Q
    is the assistant participating in the conversation.
    """

    speaker = get_person(speaker_id)

    if speaker is None:
        return None

    return {
        "speaker_id": speaker_id,
        "speaker_name": speaker["name"],

        "i": speaker_id,
        "me": speaker_id,
        "my": speaker_id,

        "you": "robot_q",
        "your": "robot_q",
    }


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    print("Robot-Q People Tool Test")
    print()

    print(
        "Camille:",
        get_person("camille")
    )

    print(
        "Shelby:",
        get_person("shelby")
    )

    print()

    print(
        get_relationship_fact(
            "camille",
            "shelby"
        )
    )

    print(
        get_relationship_fact(
            "shelby",
            "camille"
        )
    )

    print(
        get_relationship_fact(
            "robot_q",
            "camille"
        )
    )

    print()

    print(
        "Speaker context:",
        get_speaker_context("camille")
    )