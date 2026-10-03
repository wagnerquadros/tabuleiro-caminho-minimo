def default_walls():
    """Mapa fixo para facilitar a repetição da demonstração em sala."""
    walls = {(r, 5) for r in range(1, 10) if r != 7}
    walls |= {(r, c) for r in range(3, 6) for c in range(9, 13)}
    walls |= {(8, c) for c in range(8, 16) if c != 12}
    walls |= {(r, c) for r in range(1, 3) for c in range(14, 17)}
    # A célula interna (9, 2) permite demonstrar um destino sem acesso.
    walls |= {(r, c) for r in range(8, 11) for c in range(1, 4)
              if r in (8, 10) or c in (1, 3)}
    return walls
