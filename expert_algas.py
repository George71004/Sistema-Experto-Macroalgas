class Regla:
    def __init__(self, id_regla, variable_objetivo, valor_objetivo, premisas):
        self.id = id_regla
        self.variable_objetivo = variable_objetivo  # Lo que la regla intenta deducir (ej: "Grupo", "Especie")
        self.valor_objetivo = valor_objetivo        # El resultado si se cumple (ej: "Clorofita", "Sargassum")
        self.premisas = premisas                    # Diccionario de condiciones {"Atributo": "Valor"}

class SistemaExpertoAlgas:
    def __init__(self):
        # 1. Base de Conocimientos: De lo general a lo específico
        self.reglas = [
            # --- REGLAS DE NIVEL 1: Contexto y Hábitat (General) ---
            Regla("R_VARAZON", "Fenomeno", "Sargazada", {"Ubicacion": "Orilla (varada)", "Temporada": "Marzo-Agosto"}),
            Regla("R_ROCOSO", "Habitat_Base", "Rocas intermareales", {"Ubicacion": "Adherida a rocas"}),
            
            # --- REGLAS DE NIVEL 2: Filo / Color (Intermedio) ---
            Regla("R_FEOfITA", "Grupo", "Alga Parda", {"Color": "Pardo"}),
            Regla("R_CLOROFITA", "Grupo", "Alga Verde", {"Color": "Verde"}),
            Regla("R_RODOFITA", "Grupo", "Alga Roja", {"Color": "Rojo"}),

            # --- REGLAS DE NIVEL 3: Especies (Específico) ---
            # Nota cómo estas reglas dependen de las variables deducidas arriba ("Fenomeno", "Grupo")
            Regla("R_SARGASSUM", "Especie", "Sargassum spp. (Sargazo)", 
                  {"Fenomeno": "Sargazada", "Grupo": "Alga Parda", "Estructura": "Vesiculas de aire"}),
            
            Regla("R_DICTYOTA", "Especie", "Dictyota spp.", 
                  {"Habitat_Base": "Rocas intermareales", "Grupo": "Alga Parda", "Forma": "Cintas dicotomas"}),
            
            Regla("R_ULVA", "Especie", "Ulva lactuca (Lechuga de mar)", 
                  {"Habitat_Base": "Rocas intermareales", "Grupo": "Alga Verde", "Forma": "Laminar"}),
            
            Regla("R_GRACILARIA", "Especie", "Gracilaria spp.", 
                  {"Ubicacion": "Bahia somera", "Grupo": "Alga Roja", "Textura": "Cartilaginosa"})
        ]
        
        self.memoria = {}
        
        # Opciones predefinidas para guiar al usuario en la consola
        self.opciones = {
            "Ubicacion": ["Orilla (varada)", "Adherida a rocas", "Bahia somera"],
            "Temporada": ["Marzo-Agosto", "Septiembre-Febrero", "Todo el año"],
            "Color": ["Verde", "Pardo", "Rojo"]
        }

    def preguntar_usuario(self, atributo):
        """Interroga al usuario mostrando opciones si están disponibles."""
        print(f"\n[?] Necesito un dato: ¿Cuál es el valor para '{atributo}'?")
        if atributo in self.opciones:
            print(f"    Opciones sugeridas: {', '.join(self.opciones[atributo])}")
            
        respuesta = input("Respuesta: ").strip().capitalize()
        return respuesta

    def deducir_variable(self, atributo_buscado):
        """
        Corazón del motor recursivo: 
        1. Revisa si ya lo sabemos.
        2. Intenta deducirlo con reglas.
        3. Si no puede deducirlo, lo pregunta.
        """
        # 1. Si ya está en memoria, no repregunta
        if atributo_buscado in self.memoria:
            return self.memoria[atributo_buscado]
        
        # 2. Busca reglas que concluyan la variable que necesitamos
        reglas_utiles = [r for r in self.reglas if r.variable_objetivo == atributo_buscado]
        
        if reglas_utiles:
            for regla in reglas_utiles:
                premisas_cumplidas = True
                
                # Evalúa cada premisa de la regla recursivamente
                for premisa_attr, premisa_valor in regla.premisas.items():
                    # Aquí el sistema hace magia: si necesita "Fenomeno", llamará a deducir_variable("Fenomeno")
                    valor_obtenido = self.deducir_variable(premisa_attr)
                    
                    if valor_obtenido != premisa_valor.capitalize() and valor_obtenido != premisa_valor:
                        premisas_cumplidas = False
                        break # Esta regla falló, salta a la siguiente regla útil
                
                if premisas_cumplidas:
                    print(f"    [!] Deducción interna: {atributo_buscado} = {regla.valor_objetivo}")
                    self.memoria[atributo_buscado] = regla.valor_objetivo
                    return regla.valor_objetivo
                    
        # 3. Si no hay reglas para deducirlo (o todas fallaron), es un dato base: se le pregunta al usuario.
        valor_ingresado = self.preguntar_usuario(atributo_buscado)
        self.memoria[atributo_buscado] = valor_ingresado
        return valor_ingresado

    def iniciar_diagnostico(self):
        print("=== Sistema Experto: Identificación de Macroalgas ===")
        
        # Extraemos todas las posibles especies a probar
        especies_posibles = [r.valor_objetivo for r in self.reglas if r.variable_objetivo == "Especie"]
        
        for especie in especies_posibles:
            # Forzamos al motor a intentar deducir "Especie" verificando cada regla final
            regla_especie = next(r for r in self.reglas if r.valor_objetivo == especie)
            
            es_esta_especie = True
            for attr, val in regla_especie.premisas.items():
                if self.deducir_variable(attr) != val:
                    es_esta_especie = False
                    break
            
            if es_esta_especie:
                print(f"\n>>> ¡CONCLUSIÓN ALCANZADA! <<<")
                print(f"El espécimen analizado corresponde a: {especie}")
                return
                
        print("\n>>> RESULTADO DESCONOCIDO <<<")
        print("El espécimen no coincide con la base de datos actual.")

if __name__ == "__main__":
    motor = SistemaExpertoAlgas()
    motor.iniciar_diagnostico()