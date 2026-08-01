"""Interactively test the Fressnapf Tracker email login flow."""

# ruff: noqa: T201

import asyncio
from getpass import getpass

from fressnapftracker import AuthClient


async def main() -> None:
    """Authenticate by email and print the available tracker devices."""
    email = input("Fressnapf email: ").strip()
    password = getpass("Fressnapf password: ")

    async with AuthClient() as auth:
        response = await auth.request_magic_link(email, password)
        user_id = response.user.id
        access_token = response.user_token.access_token
        customer_id = response.user.additional_parameters.fressnapf_id

        while True:
            input("Open the magic link from the email, then press Enter: ")
            if await auth.check_magic_link_was_clicked(access_token):
                break
            print("The magic link has not been confirmed yet. Please try again.")

        await auth.complete_magic_link(user_id, access_token, customer_id)
        devices = await auth.get_devices(user_id, access_token)

    if not devices:
        print("No tracker devices found.")
        return

    print("Available tracker devices:")
    for device in devices:
        print(f"- Serial number: {device.serialnumber}")
        print(f"  Device token: {device.token}")


if __name__ == "__main__":
    asyncio.run(main())
