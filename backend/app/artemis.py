import json
from typing import Any

import httpx


class ArtemisError(RuntimeError):
    pass


class ArtemisManager:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
    ):
        self.url = url
        self.username = username
        self.password = password

        self.mbean = 'org.apache.activemq.artemis:broker="0.0.0.0"'

    async def exec(
        self,
        operation: str,
        arguments: list[Any] | None = None,
    ):
        payload = {
            "type": "exec",
            "mbean": self.mbean,
            "operation": operation,
            "arguments": arguments or [],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url,
                    json=payload,
                    auth=(self.username, self.password),
                )

        except httpx.HTTPError as exc:
            raise ArtemisError(
                f"Failed to connect to Artemis Jolokia at "
                f"{self.url}: {exc}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise ArtemisError(
                f"Artemis returned invalid JSON "
                f"(HTTP {response.status_code}): "
                f"{response.text}"
            ) from exc

        if response.status_code >= 400:
            raise ArtemisError(
                f"Artemis Jolokia HTTP "
                f"{response.status_code}: {data}"
            )

        if data.get("status", 200) >= 400:
            raise ArtemisError(str(data))

        if "error_type" in data or "error" in data:
            raise ArtemisError(str(data))

        return data.get("value")

    # ------------------------------------------------------------------
    # USERS
    # ------------------------------------------------------------------

    async def create_user(
        self,
        username: str,
        password: str,
        role: str,
    ):
        return await self.exec(
            "addUser("
            "java.lang.String,"
            "java.lang.String,"
            "java.lang.String,"
            "boolean"
            ")",
            [
                username,
                password,
                role,
                True,
            ],
        )

    async def remove_user(
        self,
        username: str,
    ):
        return await self.exec(
            "removeUser(java.lang.String)",
            [username],
        )

    # ------------------------------------------------------------------
    # QUEUES
    # ------------------------------------------------------------------

    async def create_queue(
        self,
        name: str,
        address: str,
        durable: bool = True,
    ):
        """
        Create an ANYCAST queue.

        Artemis 2.57 exposes:

            createQueue(
                String address,
                String name,
                boolean durable,
                String routingType
            )

        routingType must be "ANYCAST" or "MULTICAST".
        """

        return await self.exec(
            "createQueue("
            "java.lang.String,"
            "java.lang.String,"
            "boolean,"
            "java.lang.String"
            ")",
            [
                address,
                name,
                durable,
                "ANYCAST",
            ],
        )

    async def delete_queue(
        self,
        name: str,
    ):
        return await self.exec(
            "destroyQueue(java.lang.String,boolean)",
            [
                name,
                True,
            ],
        )

    async def queue_names(self):
        return await self.exec(
            "getQueueNames(java.lang.String)",
            [
                "ANYCAST",
            ],
        )

    # ------------------------------------------------------------------
    # SECURITY / ACL
    # ------------------------------------------------------------------

    async def grant_queue_acl(
        self,
        address: str,
        username: str,
        can_produce: bool,
        can_consume: bool,
    ):
        """
        Configure Artemis security settings for this address.

        Artemis expects:

        {
            "send": ["role"],
            "consume": ["role"],
            "createDurableQueue": ["role"],
            "createAddress": ["role"]
        }
        """

        security_settings: dict[str, list[str]] = {
            "createAddress": [
                username,
            ],
            "createDurableQueue": [
                username,
            ],
        }

        if can_produce:
            security_settings["send"] = [
                username,
            ]

        if can_consume:
            security_settings["consume"] = [
                username,
            ]

        roles_json = json.dumps(
            security_settings
        )

        return await self.exec(
            "addSecuritySettings("
            "java.lang.String,"
            "java.lang.String"
            ")",
            [
                address,
                roles_json,
            ],
        )

    async def queue_roles(
        self,
        address: str,
    ):
        """
        Return Artemis security roles configured
        for the supplied address.
        """

        return await self.exec(
            "getRolesAsJSON(java.lang.String)",
            [
                address,
            ],
        )

    # ------------------------------------------------------------------
    # BROKER
    # ------------------------------------------------------------------

    async def broker_version(self):
        return await self.exec(
            "getVersion()",
            [],
        )