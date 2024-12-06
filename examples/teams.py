from pathlib import Path

from rson import load


HERE = Path(__file__).parent.resolve()


with open(f"{HERE}/teams.rson") as f:
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
