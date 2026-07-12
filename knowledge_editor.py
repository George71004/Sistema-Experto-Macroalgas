import json
import os
import sys

class KnowledgeBaseEditor:
    def __init__(self, filepath="algae_knowledge.json"):
        self.filepath = filepath
        if not os.path.isabs(self.filepath):
            self.filepath = os.path.join(os.path.dirname(__file__), self.filepath)
        self.kb = {}
        self.load_kb()

    def load_kb(self):
        if not os.path.exists(self.filepath):
            print(f"[!] Archivo no encontrado en {self.filepath}. Inicializando base de conocimiento vacía.")
            self.kb = {}
            return
        with open(self.filepath, 'r', encoding='utf-8') as f:
            try:
                self.kb = json.load(f)
            except json.JSONDecodeError as e:
                print(f"[!] Error al parsear JSON: {e}")
                sys.exit(1)

    def save_kb(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.kb, f, indent=4, ensure_ascii=False)
        print(f"[✓] Cambios guardados con éxito en {self.filepath}")

    def validate_integrity(self):
        print("\n" + "="*50)
        print("REPORTE DE INTEGRIDAD DE LA BASE DE CONOCIMIENTO")
        print("="*50)
        
        errors = 0
        warnings = 0

        # 1. Verificar nodo raíz
        if "root" not in self.kb:
            print("[CRÍTICO] No se encontró el nodo raíz ('root'). El motor no podrá iniciar.")
            errors += 1
        else:
            print("[OK] Nodo raíz ('root') presente.")

        # 2. Encontrar referencias rotas y verificar estructura básica
        referenced_nodes = set()
        for node_id, node in self.kb.items():
            if node.get("is_leaf", False):
                # Validar estructura hoja
                if "species_name" not in node:
                    print(f"[ERROR] Especie '{node_id}' no posee la clave obligatoria 'species_name'.")
                    errors += 1
            else:
                # Validar estructura decisión
                required = ["question", "yes_branch", "no_branch", "character_name"]
                for req in required:
                    if req not in node:
                        print(f"[ERROR] Nodo de decisión '{node_id}' no posee la clave obligatoria '{req}'.")
                        errors += 1
                
                # Rastrear referencias
                yes_b = node.get("yes_branch")
                no_b = node.get("no_branch")
                
                if yes_b:
                    referenced_nodes.add(yes_b)
                    if yes_b not in self.kb:
                        print(f"[ERROR] Referencia rota: El nodo '{node_id}' apunta a 'yes_branch'='{yes_b}', que no existe.")
                        errors += 1
                if no_b:
                    referenced_nodes.add(no_b)
                    if no_b not in self.kb:
                        print(f"[ERROR] Referencia rota: El nodo '{node_id}' apunta a 'no_branch'='{no_b}', que no existe.")
                        errors += 1

        # 3. Detectar ciclos e inalcanzables usando recorrido DFS
        visited = set()
        has_cycle = False

        def detect_cycles(node_id, path_stack):
            nonlocal has_cycle
            if not node_id or node_id not in self.kb:
                return
            if node_id in path_stack:
                print(f"[ERROR] Ciclo infinito detectado: {' -> '.join(path_stack)} -> {node_id}")
                has_cycle = True
                return
            if node_id in visited:
                return
            
            visited.add(node_id)
            node = self.kb[node_id]
            if not node.get("is_leaf", False):
                path_stack.append(node_id)
                detect_cycles(node.get("yes_branch"), path_stack)
                detect_cycles(node.get("no_branch"), path_stack)
                path_stack.pop()

        if "root" in self.kb:
            detect_cycles("root", [])

        if has_cycle:
            errors += 1
        else:
            print("[OK] Grafo libre de ciclos de inferencia infinitos.")

        # 4. Encontrar nodos huérfanos (cargados pero inalcanzables)
        all_keys = set(self.kb.keys())
        orphans = all_keys - visited
        if orphans:
            print(f"[ADVERTENCIA] Hay {len(orphans)} nodos huérfanos (inalcanzables desde 'root'):")
            for o in sorted(orphans):
                node_type = "Especie" if self.kb[o].get("is_leaf") else "Pregunta"
                print(f"  - [{node_type}] {o}")
            warnings += len(orphans)
        else:
            print("[OK] Todos los nodos son alcanzables desde 'root'.")

        print("="*50)
        print(f"Validación finalizada: {errors} Errores, {warnings} Advertencias.")
        print("="*50 + "\n")
        return errors == 0

    def print_tree_visual(self, start_node="root", max_depth=15):
        print("\n" + "="*50)
        print(f"REPRESENTACIÓN GRÁFICA DEL ARBOL DESDE '{start_node}'")
        print("="*50)
        
        visited = set()
        
        def recurse(node_id, prefix="", is_yes=True, depth=0):
            if depth > max_depth:
                print(f"{prefix}└── ... (Profundidad máxima alcanzada)")
                return
            if not node_id:
                return
            if node_id in visited:
                print(f"{prefix}└── [{ 'SÍ' if is_yes else 'NO' }] --> {node_id} (BUCLE DETECTADO)")
                return
            
            visited.add(node_id)
            node = self.kb.get(node_id)
            if not node:
                print(f"{prefix}└── [{ 'SÍ' if is_yes else 'NO' }] --> {node_id} (ERROR: NODO NO EXISTE)")
                return
            
            branch_label = "SÍ" if is_yes else "NO"
            if node.get("is_leaf", False):
                print(f"{prefix}└── [{branch_label}] 🍁 \033[32m{node.get('species_name', node_id)}\033[0m (ID: {node_id})")
            else:
                print(f"{prefix}├── [{branch_label}] ❓ \033[36m{node.get('question')}\033[0m (ID: {node_id}) [caracter: {node.get('character_name')}]")
                new_prefix = prefix + "│   "
                recurse(node.get("yes_branch"), new_prefix, True, depth + 1)
                recurse(node.get("no_branch"), new_prefix, False, depth + 1)

        recurse(start_node)
        print("="*50 + "\n")

    def edit_or_add_node(self):
        node_id = input("\n[?] Ingrese el ID del nodo a crear o modificar: ").strip()
        if not node_id:
            print("[!] ID inválido.")
            return

        exists = node_id in self.kb
        if exists:
            print(f"[i] El nodo '{node_id}' ya existe. Cargando datos para edición...")
            node = self.kb[node_id]
        else:
            print(f"[i] Creando nuevo nodo '{node_id}'...")
            node = {}

        is_leaf_input = input("[?] ¿Es un nodo terminal de Especie? (s/n): ").strip().lower()
        is_leaf = is_leaf_input == 's'

        if is_leaf:
            # Crear/Editar especie
            node["is_leaf"] = True
            node["species_name"] = input(f"Nombre Científico ({node.get('species_name', 'Nuevo')}): ").strip() or node.get("species_name", "")
            node["phylum"] = input(f"Phylum [Chlorophyta/Heterokontophyta/Rhodophyta] ({node.get('phylum', '')}): ").strip() or node.get("phylum", "Rhodophyta")
            node["order"] = input(f"Orden ({node.get('order', '')}): ").strip() or node.get("order", "N/A")
            node["family"] = input(f"Familia ({node.get('family', '')}): ").strip() or node.get("family", "N/A")
            node["description"] = input(f"Descripción botánica ({node.get('description', '')}): ").strip() or node.get("description", "")
            node["habitat_note"] = input(f"Nota de Hábitat en Margarita ({node.get('habitat_note', '')}): ").strip() or node.get("habitat_note", "")
            
            # Filtros ambientales
            print("\n--- Perfil Ambiental ---")
            env = node.get("env_profile", {})
            
            pref_stations_raw = input(f"Estaciones preferidas (separadas por comas, ej. 1,2) ({','.join(map(str, env.get('preferred_stations', [])))}): ").strip()
            if pref_stations_raw:
                env["preferred_stations"] = [int(x.strip()) for x in pref_stations_raw.split(",") if x.strip().isdigit()]
            else:
                env["preferred_stations"] = env.get("preferred_stations", [1, 2, 3, 4])
                
            pref_months_raw = input(f"Meses preferidos (separados por comas, ej. M1,M2) ({','.join(env.get('preferred_months', []))}): ").strip()
            if pref_months_raw:
                env["preferred_months"] = [x.strip() for x in pref_months_raw.split(",") if x.strip()]
            else:
                env["preferred_months"] = env.get("preferred_months", ["M1", "M2", "M3", "M4", "M5", "M6"])

            t_min = input(f"Temperatura mínima (°C) ({env.get('temp_range', [25.0, 32.0])[0]}): ").strip()
            t_max = input(f"Temperatura máxima (°C) ({env.get('temp_range', [25.0, 32.0])[1]}): ").strip()
            env["temp_range"] = [float(t_min) if t_min else env.get("temp_range", [25.0, 32.0])[0], 
                                 float(t_max) if t_max else env.get("temp_range", [25.0, 32.0])[1]]

            s_min = input(f"Salinidad mínima (ups) ({env.get('salinity_range', [30.0, 42.0])[0]}): ").strip()
            s_max = input(f"Salinidad máxima (ups) ({env.get('salinity_range', [30.0, 42.0])[1]}): ").strip()
            env["salinity_range"] = [float(s_min) if s_min else env.get("salinity_range", [30.0, 42.0])[0], 
                                     float(s_max) if s_max else env.get("salinity_range", [30.0, 42.0])[1]]

            node["env_profile"] = env
        else:
            # Crear/Editar pregunta de decisión
            node["is_leaf"] = False
            node["question"] = input(f"Pregunta diagnóstica dicotómica ({node.get('question', '¿...?')}): ").strip() or node.get("question", "")
            node["character_name"] = input(f"Nombre de la propiedad / carácter ({node.get('character_name', '')}): ").strip() or node.get("character_name", "")
            
            yes_b = input(f"Nodo de destino si SÍ (yes_branch) ({node.get('yes_branch', '')}): ").strip()
            if yes_b:
                node["yes_branch"] = yes_b
                if yes_b not in self.kb:
                    print(f"[ADVERTENCIA] El nodo de destino '{yes_b}' no existe en la BD aún.")
            
            no_b = input(f"Nodo de destino si NO (no_branch) ({node.get('no_branch', '')}): ").strip()
            if no_b:
                node["no_branch"] = no_b
                if no_b not in self.kb:
                    print(f"[ADVERTENCIA] El nodo de destino '{no_b}' no existe en la BD aún.")

        self.kb[node_id] = node
        print(f"[✓] Nodo '{node_id}' actualizado en memoria.")

    def delete_node(self):
        node_id = input("\n[?] Ingrese el ID del nodo a eliminar: ").strip()
        if node_id not in self.kb:
            print("[!] El nodo no existe.")
            return

        # Rastrear dependencias (nodos que apuntan a este)
        referencing = []
        for k, v in self.kb.items():
            if not v.get("is_leaf", False):
                if v.get("yes_branch") == node_id:
                    referencing.append((k, "yes_branch"))
                if v.get("no_branch") == node_id:
                    referencing.append((k, "no_branch"))

        if referencing:
            print(f"[!] ADVERTENCIA: El nodo '{node_id}' está referenciado por los siguientes nodos:")
            for parent, branch in referencing:
                print(f"  - '{parent}' a través de su rama '{branch}'")
            confirm = input("[?] Si eliminas este nodo, crearás referencias rotas. ¿Deseas continuar? (s/n): ").strip().lower()
            if confirm != 's':
                print("[!] Operación cancelada.")
                return

        del self.kb[node_id]
        print(f"[✓] Nodo '{node_id}' eliminado en memoria.")

    def view_node_details(self):
        node_id = input("\n[?] Ingrese el ID del nodo a consultar: ").strip()
        if node_id not in self.kb:
            print("[!] El nodo no existe.")
            return
        print("\n" + "-"*40)
        print(f"DETALLE DEL NODO: {node_id}")
        print("-"*40)
        print(json.dumps(self.kb[node_id], indent=2, ensure_ascii=False))
        print("-"*40)

def main():
    editor = KnowledgeBaseEditor()
    
    while True:
        print("\n" + "="*50)
        print("EDITOR ADMINISTRATIVO DE BASE DE CONOCIMIENTO (FICOLOGÍA)")
        print("="*50)
        print(" [1] Visualizar Árbol de Decisión (Grafo)")
        print(" [2] Validar Integridad de la Base de Conocimiento")
        print(" [3] Agregar o Editar un Nodo (Pregunta o Especie)")
        print(" [4] Eliminar un Nodo")
        print(" [5] Ver Detalle de un Nodo")
        print(" [6] Salir y Guardar Cambios")
        print(" [7] Salir sin Guardar")
        print("="*50)
        
        choice = input("[?] Seleccione una opción: ").strip()
        
        if choice == '1':
            start = input("[?] Nodo de partida (dejar vacío para 'root'): ").strip() or "root"
            editor.print_tree_visual(start)
        elif choice == '2':
            editor.validate_integrity()
        elif choice == '3':
            editor.edit_or_add_node()
        elif choice == '4':
            editor.delete_node()
        elif choice == '5':
            editor.view_node_details()
        elif choice == '6':
            editor.validate_integrity()
            confirm = input("[?] ¿Está seguro de guardar todos los cambios? (s/n): ").strip().lower()
            if confirm == 's':
                editor.save_kb()
                break
        elif choice == '7':
            confirm = input("[?] ¿Desea salir sin guardar los cambios del editor? (s/n): ").strip().lower()
            if confirm == 's':
                print("[i] Saliendo sin guardar.")
                break
        else:
            print("[!] Opción inválida.")

if __name__ == "__main__":
    main()
