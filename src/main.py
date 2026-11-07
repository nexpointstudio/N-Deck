
import sys
from pathlib import Path

import flet as ft
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from services.tcgdex_api import search_cards, get_card, card_image


# N-DECK — DESIGN SYSTEM
RED = "#E53935"
RED_DARK = "#B71C1C"
RED_LIGHT = "#FFF0EF"
BLACK = "#18191D"
SIDEBAR = "#191A20"
WHITE = "#FFFFFF"
BACKGROUND = "#F6F7F9"
GRAY = "#737782"
BORDER = "#E9EAEE"


def label(text, size=14, color=BLACK, bold=False):
    return ft.Text(
        text,
        size=size,
        color=color,
        weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
    )


def main(page: ft.Page):
    page.title = "N-Deck | Pokémon TCG"
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.spacing = 0
    page.theme_mode = ft.ThemeMode.LIGHT

    current_screen = "home"
    search_text = ""
    search_page = 1
    cards = []
    selected_card = None
    loading = False
    searched = False
    error_message = ""

    NAV = [
        ("home", "Início", ft.Icons.HOME_ROUNDED),
        ("catalog", "Catálogo", ft.Icons.SEARCH_ROUNDED),
        ("collection", "Minha coleção", ft.Icons.STYLE_ROUNDED),
        ("trades", "Trocas", ft.Icons.SWAP_HORIZ_ROUNDED),
        ("wishlist", "Desejos", ft.Icons.FAVORITE_BORDER_ROUNDED),
    ]

    def panel(content, padding=22, bgcolor=WHITE):
        return ft.Container(
            bgcolor=bgcolor,
            border_radius=20,
            padding=padding,
            content=content,
        )

    def heading(title, description):
        return ft.Column(
            spacing=5,
            controls=[
                label(title, 27, BLACK, True),
                label(description, 13, GRAY),
            ],
        )

    def action(text, callback, icon=None, primary=True):
        return ft.Button(
            content=text,
            icon=icon,
            bgcolor=RED if primary else WHITE,
            color=WHITE if primary else BLACK,
            on_click=callback,
        )

    def empty_state(icon, title, description, button=None):
        controls = [
            ft.Container(
                bgcolor=RED_LIGHT,
                border_radius=20,
                padding=24,
                content=ft.Icon(icon, size=44, color=RED),
            ),
            label(title, 21, BLACK, True),
            ft.Text(
                description,
                color=GRAY,
                size=14,
                text_align=ft.TextAlign.CENTER,
            ),
        ]

        if button:
            controls.append(button)

        return panel(
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=18,
                controls=controls,
            ),
            padding=45,
        )

    def sidebar_item(screen, text, icon):
        active = current_screen == screen

        container = ft.Container(
            bgcolor=RED if active else SIDEBAR,
            border_radius=12,
            padding=14,
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(
                        icon,
                        size=20,
                        color=WHITE if active else "#A7AAB4",
                    ),
                    label(
                        text,
                        14,
                        WHITE if active else "#A7AAB4",
                        active,
                    ),
                ],
            ),
            animate=ft.Animation(
                180, ft.AnimationCurve.EASE_OUT
            ),
            on_click=lambda e: navigate(screen),
        )

        def hover(e):
            if not active:
                container.bgcolor = (
                    "#30313A" if e.data == "true" else SIDEBAR
                )
                container.update()

        container.on_hover = hover
        return container

    def build_sidebar():
        return ft.Container(
            width=230,
            bgcolor=SIDEBAR,
            padding=18,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Container(
                        padding=ft.Padding(
                            left=8, top=14, right=0, bottom=30
                        ),
                        content=ft.Row(
                            spacing=10,
                            controls=[
                                ft.Container(
                                    bgcolor=RED,
                                    border_radius=12,
                                    padding=11,
                                    content=ft.Icon(
                                        ft.Icons.STYLE,
                                        color=WHITE,
                                        size=25,
                                    ),
                                ),
                                ft.Column(
                                    spacing=1,
                                    controls=[
                                        label("N-DECK", 21, WHITE, True),
                                        label(
                                            "POKÉMON TCG",
                                            10,
                                            "#A7AAB4",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                    *[
                        sidebar_item(screen, text, icon)
                        for screen, text, icon in NAV
                    ],
                    ft.Container(expand=True),
                    ft.Divider(color="#383A44"),
                    ft.Container(
                        padding=10,
                        content=ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(
                                    ft.Icons.CLOUD_OUTLINED,
                                    color="#A7AAB4",
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        label(
                                            "Nuvem não conectada",
                                            11,
                                            WHITE,
                                            True,
                                        ),
                                        label(
                                            "Supabase: próxima etapa",
                                            10,
                                            "#A7AAB4",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def build_home():
        return ft.Column(
            spacing=22,
            controls=[
                heading(
                    "Bem-vindo ao N-Deck",
                    "Seu espaço para descobrir e organizar cartas Pokémon.",
                ),
                ft.Container(
                    border_radius=22,
                    padding=30,
                    bgcolor=RED,
                    content=ft.Column(
                        spacing=16,
                        controls=[
                            label(
                                "O universo Pokémon na sua coleção.",
                                29,
                                WHITE,
                                True,
                            ),
                            label(
                                "Pesquise cartas reais, explore expansões "
                                "e prepare sua coleção digital.",
                                15,
                                "#FFE4E2",
                            ),
                            ft.Row(
                                controls=[
                                    action(
                                        "Explorar catálogo",
                                        lambda e: navigate("catalog"),
                                        ft.Icons.ARROW_FORWARD,
                                        primary=False,
                                    )
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Row(
                    spacing=14,
                    controls=[
                        stat_box(
                            "Cartas cadastradas",
                            "—",
                            ft.Icons.STYLE,
                        ),
                        stat_box(
                            "Valor da coleção",
                            "—",
                            ft.Icons.SHOW_CHART,
                        ),
                        stat_box(
                            "Trocas pendentes",
                            "—",
                            ft.Icons.SWAP_HORIZ,
                        ),
                    ],
                ),
                panel(
                    ft.Column(
                        spacing=14,
                        controls=[
                            label(
                                "Comece sua coleção", 19, BLACK, True
                            ),
                            label(
                                "O catálogo já está conectado à TCGdex. "
                                "Suas cartas pessoais serão armazenadas "
                                "após configurarmos as contas.",
                                14,
                                GRAY,
                            ),
                            action(
                                "Pesquisar cartas",
                                lambda e: navigate("catalog"),
                                ft.Icons.SEARCH,
                            ),
                        ],
                    )
                ),
            ],
        )

    def stat_box(title, value, icon):
        return ft.Container(
            expand=True,
            bgcolor=WHITE,
            border_radius=18,
            padding=20,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icon, color=RED, size=22),
                            label(title, 12, GRAY),
                        ],
                    ),
                    label(value, 27, BLACK, True),
                ],
            ),
        )

    def image_control(card, width=165, height=225, high=False):
        url = card_image(
            card, "high" if high else "low"
        )

        if not url:
            return ft.Container(
                width=width,
                height=height,
                alignment=ft.Alignment.CENTER,
                bgcolor=BACKGROUND,
                border_radius=10,
                content=label("Sem imagem", 12, GRAY),
            )

        return ft.Image(
            src=url,
            width=width,
            height=height,
            fit=ft.BoxFit.CONTAIN,
            error_content=ft.Container(
                width=width,
                height=height,
                bgcolor=BACKGROUND,
                alignment=ft.Alignment.CENTER,
                content=label(
                    "Imagem indisponível", 11, GRAY
                ),
            ),
        )

    def card_widget(card):
        box = ft.Container(
            width=205,
            bgcolor=WHITE,
            padding=15,
            border_radius=18,
            animate=ft.Animation(
                180, ft.AnimationCurve.EASE_OUT
            ),
            on_click=lambda e, cid=card["id"]: page.run_task(
                open_details, cid
            ),
            content=ft.Column(
                spacing=9,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    image_control(card),
                    ft.Text(
                        card.get("name") or "Sem nome",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=BLACK,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                    ),
                    label(
                        "Nº " + str(card.get("localId", "?")),
                        12,
                        GRAY,
                    ),
                    ft.Container(
                        bgcolor=RED_LIGHT,
                        border_radius=9,
                        padding=8,
                        alignment=ft.Alignment.CENTER,
                        content=label(
                            "Ver detalhes", 12, RED, True
                        ),
                    ),
                ],
            ),
        )

        def hover(e):
            box.bgcolor = (
                "#FFF4F3" if e.data == "true" else WHITE
            )
            box.update()

        box.on_hover = hover
        return box

    def build_catalog():
        search_field = ft.TextField(
            value=search_text,
            hint_text="Pikachu, Charizard, Mewtwo...",
            border_radius=12,
            expand=True,
            on_submit=lambda e: page.run_task(
                perform_search, search_field.value, 1
            ),
        )

        search_bar = panel(
            ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(
                        ft.Icons.SEARCH,
                        color=RED,
                        size=25,
                    ),
                    search_field,
                    action(
                        "Pesquisar",
                        lambda e: page.run_task(
                            perform_search,
                            search_field.value,
                            1,
                        ),
                        ft.Icons.ARROW_FORWARD,
                    ),
                ],
            ),
            padding=15,
        )

        controls = [
            heading(
                "Catálogo Pokémon",
                "Explore cartas de diferentes expansões.",
            ),
            search_bar,
        ]

        if loading:
            controls.append(
                panel(
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=14,
                        controls=[
                            ft.ProgressRing(color=RED),
                            label(
                                "Buscando cartas na TCGdex...",
                                14,
                                GRAY,
                            ),
                        ],
                    ),
                    padding=35,
                )
            )

        elif selected_card:
            controls.append(build_details(selected_card))

        elif cards:
            controls.extend([
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        label(
                            f"{len(cards)} cartas nesta página",
                            14,
                            GRAY,
                        ),
                        label(
                            f"Página {search_page}",
                            13,
                            RED,
                            True,
                        ),
                    ],
                ),
                ft.Row(
                    wrap=True,
                    spacing=15,
                    run_spacing=15,
                    controls=[
                        card_widget(card) for card in cards
                    ],
                ),
                ft.Row(
                    spacing=12,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Button(
                            "Anterior",
                            disabled=search_page <= 1,
                            on_click=lambda e: page.run_task(
                                perform_search,
                                search_text,
                                search_page - 1,
                            ),
                        ),
                        label(
                            f"Página {search_page}",
                            13,
                            BLACK,
                            True,
                        ),
                        ft.Button(
                            "Próxima",
                            disabled=len(cards) < 24,
                            on_click=lambda e: page.run_task(
                                perform_search,
                                search_text,
                                search_page + 1,
                            ),
                        ),
                    ],
                ),
            ])

        elif error_message:
            controls.append(
                empty_state(
                    ft.Icons.ERROR_OUTLINE,
                    "Não foi possível carregar",
                    error_message,
                )
            )

        elif searched:
            controls.append(
                empty_state(
                    ft.Icons.SEARCH_OFF,
                    "Nenhuma carta encontrada",
                    "Tente pesquisar outro nome.",
                )
            )

        else:
            controls.append(
                empty_state(
                    ft.Icons.STYLE_OUTLINED,
                    "Seu próximo Pokémon está aqui",
                    "Digite um nome para explorar o catálogo.",
                )
            )

        return ft.Column(
            spacing=20,
            controls=controls,
        )

    def build_details(card):
        expansion = card.get("set") or {}
        rarity = card.get("rarity") or "Não informada"

        information = ft.Column(
            spacing=14,
            controls=[
                label(
                    card.get("name") or "Carta Pokémon",
                    27,
                    RED,
                    True,
                ),
                info_row("Identificador", card.get("id", "—")),
                info_row(
                    "Número",
                    str(card.get("localId") or "—"),
                ),
                info_row(
                    "Expansão",
                    expansion.get("name") or "Não informada",
                ),
                info_row("Raridade", rarity),
                ft.Divider(color=BORDER),
                label(
                    "Valores de mercado e adição à coleção "
                    "serão integrados nas próximas etapas.",
                    13,
                    GRAY,
                ),
            ],
        )

        return panel(
            ft.Column(
                spacing=20,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            label(
                                "Detalhes da carta",
                                20,
                                BLACK,
                                True,
                            ),
                            action(
                                "Voltar ao catálogo",
                                lambda e: close_details(),
                                ft.Icons.ARROW_BACK,
                                primary=False,
                            ),
                        ],
                    ),
                    ft.Divider(color=BORDER),
                    ft.Row(
                        wrap=True,
                        spacing=28,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            image_control(
                                card, 260, 355, high=True
                            ),
                            ft.Container(
                                width=350,
                                content=information,
                            ),
                        ],
                    ),
                ],
            ),
            padding=24,
        )

    def info_row(title, value):
        return ft.Column(
            spacing=3,
            controls=[
                label(title, 12, GRAY),
                label(str(value), 15, BLACK, True),
            ],
        )

    def build_collection():
        return ft.Column(
            spacing=20,
            controls=[
                heading(
                    "Minha coleção",
                    "Seu álbum digital de cartas Pokémon.",
                ),
                empty_state(
                    ft.Icons.STYLE_OUTLINED,
                    "Seu álbum está vazio",
                    "Em breve você poderá guardar suas cartas "
                    "e sincronizá-las entre PC e celular.",
                    action(
                        "Explorar catálogo",
                        lambda e: navigate("catalog"),
                        ft.Icons.SEARCH,
                    ),
                ),
            ],
        )

    def build_trades():
        return ft.Column(
            spacing=20,
            controls=[
                heading(
                    "Central de trocas",
                    "Propostas e negociações entre colecionadores.",
                ),
                empty_state(
                    ft.Icons.SWAP_HORIZ,
                    "Central de trocas em preparação",
                    "Aqui vocês poderão oferecer cartas, "
                    "comparar valores e aceitar ou recusar "
                    "propostas. A função será ativada "
                    "após a configuração das contas.",
                ),
            ],
        )

    def build_wishlist():
        return ft.Column(
            spacing=20,
            controls=[
                heading(
                    "Lista de desejos",
                    "As cartas que você quer encontrar.",
                ),
                empty_state(
                    ft.Icons.FAVORITE_BORDER,
                    "Sua lista está vazia",
                    "Após integrar o banco de dados, "
                    "você poderá acompanhar as cartas "
                    "que pretende adquirir.",
                    action(
                        "Explorar cartas",
                        lambda e: navigate("catalog"),
                        ft.Icons.SEARCH,
                    ),
                ),
            ],
        )

    def build_screen():
        screens = {
            "home": build_home,
            "catalog": build_catalog,
            "collection": build_collection,
            "trades": build_trades,
            "wishlist": build_wishlist,
        }

        return ft.Container(
            padding=25,
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                controls=[screens[current_screen]()],
            ),
        )

    def refresh_screen():
        sidebar_holder.content = build_sidebar()
        switcher.content = build_screen()
        page.update()

    def navigate(screen):
        nonlocal current_screen, selected_card

        if screen == current_screen:
            return

        current_screen = screen
        selected_card = None
        refresh_screen()

    def close_details():
        nonlocal selected_card
        selected_card = None
        refresh_screen()

    async def open_details(card_id):
        nonlocal selected_card, loading, error_message

        if loading:
            return

        loading = True
        error_message = ""
        refresh_screen()

        try:
            selected_card = await get_card(card_id)
        except Exception as exc:
            error_message = f"Falha ao abrir a carta: {exc}"
            selected_card = None
        finally:
            loading = False
            if current_screen == "catalog":
                refresh_screen()

    async def perform_search(query, target_page=1):
        nonlocal search_text, search_page
        nonlocal cards, loading, searched
        nonlocal selected_card, error_message

        if loading:
            return

        query = (query or "").strip()

        if not query:
            return

        search_text = query
        loading = True
        selected_card = None
        error_message = ""
        refresh_screen()

        try:
            found = await search_cards(
                query,
                page=target_page,
                limit=24,
            )
            cards = found
            search_page = target_page
            searched = True

        except httpx.HTTPStatusError as exc:
            cards = []
            error_message = (
                f"Erro da API: HTTP {exc.response.status_code}"
            )

        except httpx.RequestError:
            cards = []
            error_message = (
                "Sem conexão com a TCGdex. "
                "Verifique sua internet."
            )

        except Exception as exc:
            cards = []
            error_message = str(exc)

        finally:
            loading = False
            if current_screen == "catalog":
                refresh_screen()

    sidebar_holder = ft.Container(
        content=build_sidebar(),
    )

    switcher = ft.AnimatedSwitcher(
        content=build_screen(),
        expand=True,
        duration=240,
        reverse_duration=140,
        transition=ft.AnimatedSwitcherTransition.FADE,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_IN,
    )

    page.add(
        ft.Row(
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                sidebar_holder,
                ft.Container(
                    expand=True,
                    bgcolor=BACKGROUND,
                    content=switcher,
                ),
            ],
        )
    )


if __name__ == "__main__":
    ft.run(main)
