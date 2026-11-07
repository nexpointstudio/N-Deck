
import asyncio
import re

import httpx

BASE_URL = "https://api.tcgdex.net/v2/en"
TIMEOUT = 25.0


def normalize_number(value):
    value = str(value).strip()

    if value.isdigit():
        return str(int(value))

    return value.upper()


async def get_card(card_id: str):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{BASE_URL}/cards/{card_id}"
        )
        response.raise_for_status()
        return response.json()


async def search_by_number(client, number, total):
    """
    Procura uma carta pelo formato 022/086.

    Busca expansões com 86 cartas oficiais
    e procura a carta 022 dentro delas.
    """
    response = await client.get(f"{BASE_URL}/sets")
    response.raise_for_status()

    sets = response.json()

    candidates = [
        item for item in sets
        if str(
            (item.get("cardCount") or {}).get("official", "")
        ) == str(total)
    ]

    semaphore = asyncio.Semaphore(6)

    async def check_set(item):
        async with semaphore:
            response = await client.get(
                f"{BASE_URL}/sets/{item['id']}"
            )
            response.raise_for_status()

            data = response.json()

            return [
                card
                for card in data.get("cards", [])
                if normalize_number(
                    card.get("localId", "")
                ) == normalize_number(number)
            ]

    groups = await asyncio.gather(
        *(check_set(item) for item in candidates)
    )

    return [
        card
        for group in groups
        for card in group
    ]


async def search_cards(
    name: str,
    page: int = 1,
    limit: int = 24,
):
    query = name.strip()

    if not query:
        return []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:

        # Formato: 022/086
        number_match = re.fullmatch(
            r"(\d+)\s*/\s*(\d+)",
            query,
        )

        if number_match:
            number, total = number_match.groups()

            cards = await search_by_number(
                client,
                number,
                int(total),
            )

            start = (page - 1) * limit
            return cards[start:start + limit]

        # Formato: me04-022
        id_match = re.fullmatch(
            r"[A-Za-z0-9.]+-[A-Za-z0-9]+",
            query,
        )

        if id_match:
            response = await client.get(
                f"{BASE_URL}/cards/{query}"
            )

            if response.status_code == 404:
                return []

            response.raise_for_status()

            card = response.json()
            return [card] if page == 1 else []

        # Busca tradicional por nome
        response = await client.get(
            f"{BASE_URL}/cards",
            params={
                "name": query,
                "pagination:page": page,
                "pagination:itemsPerPage": limit,
            },
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise ValueError(
                "Resposta inesperada da TCGdex."
            )

        return data


def card_image(card: dict, quality: str = "low"):
    image = card.get("image")

    if not image:
        return None

    return f"{image}/{quality}.webp"
