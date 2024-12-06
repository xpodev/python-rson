# Python RSON


RSON is a superset of the JSON format. It extends JSON with the primary goal of allowing
references in the JSON itself.

In addition to that, RSON also allows:
- [x] Line comments
- [x] Block comments
- [x] Trailing commas

> These are just some nicities are not the primary goal of the RSON format.


## Usage

The RSON format allows references by adding 2 types of tokens:
1. DEF node - defines a `ref-name` for the value
2. REF node - references the given `ref-name`

The `DEF` node can be used on any JSON value. This node defines a name for the value which can then used
to refer to the same value.
The `REF` node can only appear as an *object value* or an *array member*, and is used to refer to a
defined name.

Here is an example of how this would work:
```json
// team.rson

[
    {
        "members": [
            {
                "name": "Alice",
                "role": $ROLE_DEVELOPER
            },
            {
                "name": "Bob",
                "role": $ROLE_MANAGER
            },
            {
                "name": "Charlie",
                "role": $ROLE_DESIGNER
            }
        ],
        "roles": [
            {
                "name": "Developer"
            }(ROLE_DEVELOPER),
            {
                "name": "Designer"
            }(ROLE_DESIGNER),
            {
                "name": "Manager"
            }(ROLE_MANAGER)
        ]
    }
]
```

We can load the `teams.rson` file with the following code:
```py
from rson import load

with open("teams.rson") as f:
    team = load(f)[0]

    target_role_name = input("Which role to look for? ")

    for role in team["roles"]:
        if role["name"].lower() == target_role_name.lower():
            target_role = role
            break
    else:
        print("Could not find role " + target_role_name)
        exit()

    members_with_role = [
        member for member in team["members"]
        if member["role"] is target_role # <- note the identity check here
    ]

    print(f"Found {len(members_with_role)} members with role {role['name']}:")
    for i, member in enumerate(members_with_role):
        print(f"\t{i}. {member['name']}")

```

and a sample execution:
```
Which role to look for? developer
Found 2 members with role Developer:
        0. Alice
        1. David
```

## Specification

The `ref-name` must conform to the following regex:
```re
[A-Za-z_][A-Za-z_0-9]*
```

Or, in plain english:
> The first character must be a valid english letter or an underscore, and the
> following letters must be either an english letter, an underscore or a digit.
> A `ref-name` must have at least 1 character (the first character).


A `DEF` node can be used for every JSON value, so this makes the following
valid as well:
```json
{
    "organization": {
        "name": "Xpo Development"(ORG_NAME)
    },
    "title": $ORG_NAME
}
```


## Contributing

Feel free to open an issue or a PR.

## ToDo

- [x] Implement the `load` function
- [x] Implement the `loads` function
- [ ] Implement the `dump` function
- [ ] Implement the `dumps` function
