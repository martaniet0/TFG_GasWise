def to_float(n):    
    try:
        # Reemplaza coma por punto y luego convierte el string a float
        n = n.replace(',', '.')
        n_float = float(n)
        return n_float
    except ValueError:
        return "No se pudo convertir el string a real", 400
