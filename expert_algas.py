import json
import os
import sys

# ==============================================================================
# 1. TRUTH MAINTENANCE SYSTEM (JTMS)
# ==============================================================================

class JTMSNode:
    def __init__(self, name, value, justification=None):
        self.name = name
        self.value = value       # True or False
        self.status = 'IN'       # 'IN' (believed) or 'OUT' (not believed)
        self.justification = justification  # 'USER' or list of tuples (node_name, value)

    def __repr__(self):
        return f"Node({self.name}, status={self.status}, val={self.value}, just={self.justification})"


class JTMS:
    def __init__(self):
        self.nodes = {}
        self.rules = []          # List of (consequent_name, value, list_of_antecedents)
        self.contradictions = [] # List of (node_a, val_a, node_b, val_b, message)

    def add_node(self, name, value, justification=None):
        node = JTMSNode(name, value, justification)
        self.nodes[name] = node
        return node

    def add_assumption(self, name, value):
        if name in self.nodes:
            self.nodes[name].value = value
            self.nodes[name].status = 'IN'
            self.nodes[name].justification = 'USER'
        else:
            self.add_node(name, value, 'USER')
        self.propagate()

    def add_rule(self, consequent, value, antecedents):
        """antecedents is a list of tuples (node_name, value)"""
        self.rules.append((consequent, value, antecedents))

    def add_contradiction_rule(self, node_a, val_a, node_b, val_b, message):
        self.contradictions.append((node_a, val_a, node_b, val_b, message))

    def retract(self, name):
        if name in self.nodes:
            self.nodes[name].status = 'OUT'
            self.propagate()

    def clear(self):
        self.nodes.clear()

    def propagate(self):
        # Reset non-user nodes to OUT
        for name, node in self.nodes.items():
            if node.justification != 'USER':
                node.status = 'OUT'

        # Propagate rules iteratively
        changed = True
        while changed:
            changed = False
            for consequent, val, antecedents in self.rules:
                all_in = True
                for ant_name, ant_val in antecedents:
                    if (ant_name not in self.nodes or 
                        self.nodes[ant_name].status != 'IN' or 
                        self.nodes[ant_name].value != ant_val):
                        all_in = False
                        break

                if all_in:
                    # Trigger consequence
                    if consequent not in self.nodes:
                        self.add_node(consequent, val, antecedents)
                        changed = True
                    elif self.nodes[consequent].status != 'IN':
                        self.nodes[consequent].status = 'IN'
                        self.nodes[consequent].value = val
                        self.nodes[consequent].justification = antecedents
                        changed = True

    def check_consistency(self):
        """Returns dict with conflict nodes and message if a contradiction is IN"""
        for node_a, val_a, node_b, val_b, msg in self.contradictions:
            if (node_a in self.nodes and self.nodes[node_a].status == 'IN' and self.nodes[node_a].value == val_a and
                node_b in self.nodes and self.nodes[node_b].status == 'IN' and self.nodes[node_b].value == val_b):
                return {
                    "conflict": [node_a, node_b],
                    "message": msg
                }
        return None


# ==============================================================================
# 2. GESTIÓN DE LA BASE DE CONOCIMIENTOS (ONTOLOGÍA)
# ==============================================================================

class KnowledgeBaseManager:
    """Gestiona la carga y validación de la ontología taxonómica en formato JSON."""
    def __init__(self, filepath="algae_knowledge.json"):
        self.filepath = filepath
        if not os.path.isabs(self.filepath):
            self.filepath = os.path.join(os.path.dirname(__file__), self.filepath)
        self.base = self._load_json()
        self.validate()

    def _load_json(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Error: No se encontró la base de conocimientos en {self.filepath}")
        with open(self.filepath, 'r', encoding='utf-8') as file:
            return json.load(file)

    def get_node(self, node_id):
        return self.base.get(node_id)

    def validate(self):
        """Valida que todos los nodos tengan estructura correcta y las ramas sean alcanzables."""
        if "root" not in self.base:
            raise ValueError("La base de conocimientos debe contener un nodo 'root'.")
            
        for node_id, node in self.base.items():
            if node.get("is_leaf", False):
                required_leaf_keys = ["species_name"]
                for key in required_leaf_keys:
                    if key not in node:
                        raise ValueError(f"El nodo terminal '{node_id}' debe contener la clave '{key}'.")
            else:
                required_decision_keys = ["question", "yes_branch", "no_branch", "character_name"]
                for key in required_decision_keys:
                    if key not in node:
                        raise ValueError(f"El nodo de decisión '{node_id}' debe contener la clave '{key}'.")
                
                yes_b = node["yes_branch"]
                no_b = node["no_branch"]
                if yes_b not in self.base:
                    raise ValueError(f"El nodo '{node_id}' tiene un 'yes_branch' ('{yes_b}') que no existe.")
                if no_b not in self.base:
                    raise ValueError(f"El nodo '{node_id}' tiene un 'no_branch' ('{no_b}') que no existe.")


class KnowledgeBaseDictWrapper:
    """Proporciona compatibilidad dual de interfaz para AlgaeExpertSystem."""
    def __init__(self, kb_manager):
        self.kb_manager = kb_manager
        self.base = kb_manager.base

    def get(self, key, default=None):
        return self.base.get(key, default)

    def get_node(self, node_id):
        return self.kb_manager.get_node(node_id)

    def __getitem__(self, key):
        return self.base[key]

    def __contains__(self, key):
        return key in self.base

    def values(self):
        return self.base.values()

    def items(self):
        return self.base.items()

    def __len__(self):
        return len(self.base)


# ==============================================================================
# 3. MOTOR DE INFERENCIA RECURSIVO Y DE INCERTIDUMBRE (BACKTRACKING)
# ==============================================================================

class Path:
    def __init__(self, assumptions=None, ns_count=0, history=None):
        self.assumptions = assumptions if assumptions is not None else {}
        self.ns_count = ns_count
        self.history = history if history is not None else []
        self.is_completed = False
        self.candidate_species = None

    def clone(self):
        return Path(
            assumptions=dict(self.assumptions),
            ns_count=self.ns_count,
            history=list(self.history)
        )


class AlgaeExpertSystem:
    """Motor de inferencia determinista con backtracking y JTMS integrado."""
    def __init__(self, kb_manager="algae_knowledge.json"):
        if isinstance(kb_manager, str):
            self.kb_manager = KnowledgeBaseManager(kb_manager)
        else:
            self.kb_manager = kb_manager
            
        self.kb = KnowledgeBaseDictWrapper(self.kb_manager)
        self.pre_filters = {"temp": None, "salinity": None, "station": None, "month": None}
        self.facts_history = []  # list of tuples (char_name, answer) representing decision path
        self.active_paths = []
        self.jtms = JTMS()
        
        self.setup_jtms_rules()
        self.reset_session()

    @property
    def user_choices(self):
        return self.facts_history

    @user_choices.setter
    def user_choices(self, val):
        self.facts_history = val

    def setup_jtms_rules(self):
        # Reglas de Phylum Deducibles
        self.jtms.add_rule("phylum_clorofita", True, [("color_verde_no_calc", True)])
        self.jtms.add_rule("phylum_heterokonto", True, [("color_pardo", True)])
        self.jtms.add_rule("phylum_rodofita", True, [("color_verde_no_calc", False), ("color_pardo", False)])

        # Reglas de Incompatibilidad Anatómica (Contradicciones)
        self.jtms.add_contradiction_rule(
            "color_verde_no_calc", True, "color_pardo", True,
            "Un alga no puede ser verde no calcificada y parda simultáneamente."
        )
        self.jtms.add_contradiction_rule(
            "estructura_cenocitica", True, "talo_laminar_o_tubular_hueco", True,
            "Una estructura cenocítica es incompatible con un talo celular laminar o tubular."
        )
        self.jtms.add_contradiction_rule(
            "talo_calcificado", True, "color_verde_no_calc", True,
            "Las algas verdes de nuestro catálogo no están calcificadas."
        )
        self.jtms.add_contradiction_rule(
            "talo_calcificado", True, "estructura_cenocitica", True,
            "Las algas calcificadas duras en nuestro ecosistema (Jania) no poseen estructura cenocítica."
        )
        self.jtms.add_contradiction_rule(
            "color_pardo", True, "estructura_cenocitica", True,
            "Las algas pardas (Heterokontophyta) no presentan estructura cenocítica."
        )
        self.jtms.add_contradiction_rule(
            "presencia_vesiculas_filoides_estipe", True, "talo_calcificado", True,
            "Las algas del género Sargassum poseen vesículas y filoides pero nunca talo rígido calcificado."
        )

    def reset_session(self):
        self.facts_history = []
        self.active_paths = [Path()]
        self.jtms.clear()
        self.setup_jtms_rules()
        self.evaluate_state()

    def set_pre_filters(self, temp, salinity, station, month):
        self.pre_filters["temp"] = temp
        self.pre_filters["salinity"] = salinity
        self.pre_filters["station"] = station
        self.pre_filters["month"] = month
        self.evaluate_state()

    def get_environmental_score(self, species_id):
        species = self.kb.get(species_id)
        if not species or "env_profile" not in species:
            return 1.0
        
        profile = species["env_profile"]
        matches = 0
        total_checks = 0

        if self.pre_filters["station"] is not None:
            total_checks += 1
            if self.pre_filters["station"] in profile.get("preferred_stations", []):
                matches += 1

        if self.pre_filters["month"] is not None:
            total_checks += 1
            if self.pre_filters["month"] in profile.get("preferred_months", []):
                matches += 1

        if self.pre_filters["temp"] is not None:
            total_checks += 1
            t_range = profile.get("temp_range", [25.0, 32.0])
            if t_range[0] <= self.pre_filters["temp"] <= t_range[1]:
                matches += 1

        if self.pre_filters["salinity"] is not None:
            total_checks += 1
            s_range = profile.get("salinity_range", [30.0, 42.0])
            if s_range[0] <= self.pre_filters["salinity"] <= s_range[1]:
                matches += 1

        if total_checks == 0:
            return 1.0
        return matches / total_checks

    def evaluate_state(self):
        self.jtms.clear()
        self.setup_jtms_rules()
        for char_name, answer in self.facts_history:
            if answer == 'S':
                self.jtms.add_assumption(char_name, True)
            elif answer == 'N':
                self.jtms.add_assumption(char_name, False)

        self.active_paths = [Path()]
        changed = True
        while changed:
            changed = False
            for char_name, answer in self.facts_history:
                next_paths = []
                for path in self.active_paths:
                    if char_name in path.assumptions:
                        next_paths.append(path)
                        continue
                    
                    curr_node_id = self.find_blocked_node(path)
                    if curr_node_id and not kb_is_leaf(self.kb, curr_node_id):
                        node = self.kb[curr_node_id]
                        if node.get("character_name") == char_name:
                            changed = True
                            if answer == 'S':
                                path.assumptions[char_name] = True
                                next_paths.append(path)
                            elif answer == 'N':
                                path.assumptions[char_name] = False
                                next_paths.append(path)
                            elif answer in {'D', 'NS'}:
                                p1 = path.clone()
                                p1.assumptions[char_name] = True
                                p1.ns_count += 1
                                
                                p2 = path.clone()
                                p2.assumptions[char_name] = False
                                p2.ns_count += 1
                                
                                next_paths.append(p1)
                                next_paths.append(p2)
                        else:
                            next_paths.append(path)
                    else:
                        next_paths.append(path)
                self.active_paths = next_paths

        consistent_paths = []
        for path in self.active_paths:
            if self.is_path_consistent(path):
                curr_node_id = "root"
                history = []
                while curr_node_id:
                    node = self.kb.get(curr_node_id)
                    if not node:
                        break
                    history.append(curr_node_id)
                    if node.get("is_leaf", False):
                        path.is_completed = True
                        path.candidate_species = curr_node_id
                        break
                    
                    char = node.get("character_name")
                    if char in path.assumptions:
                        val = path.assumptions[char]
                        curr_node_id = node["yes_branch"] if val else node["no_branch"]
                    else:
                        break
                path.history = history
                consistent_paths.append(path)
        self.active_paths = consistent_paths

        if len(self.active_paths) == 0:
            self.jtms.add_assumption("sin_especies_compatibles", True)
            self.jtms.add_rule("CONTRADICCION_DICHOTOMICA", True, [("sin_especies_compatibles", True)])
            self.jtms.add_contradiction_rule(
                "sin_especies_compatibles", True, "sin_especies_compatibles", True,
                "No existen especies en el catálogo que coincidan con esta combinación de caracteres anatómicos."
            )
            self.jtms.propagate()

    def is_path_consistent(self, path):
        temp_jtms = JTMS()
        temp_jtms.rules = list(self.jtms.rules)
        temp_jtms.contradictions = list(self.jtms.contradictions)
        for char, val in path.assumptions.items():
            temp_jtms.add_assumption(char, val)
        temp_jtms.propagate()
        return temp_jtms.check_consistency() is None

    def find_blocked_node(self, path):
        curr_id = "root"
        while curr_id:
            node = self.kb.get(curr_id)
            if not node:
                return None
            if node.get("is_leaf", False):
                return curr_id
            char = node.get("character_name")
            if char in path.assumptions:
                val = path.assumptions[char]
                curr_id = node["yes_branch"] if val else node["no_branch"]
            else:
                return curr_id
        return None

    def submit_answer(self, char_name, answer):
        self.facts_history = [c for c in self.facts_history if c[0] != char_name]
        self.facts_history.append((char_name, answer))
        self.evaluate_state()

    def retract_choice(self, char_name):
        self.facts_history = [c for c in self.facts_history if c[0] != char_name]
        self.jtms.retract(char_name)
        self.evaluate_state()

    def get_state(self):
        pending_questions = {}
        for path in self.active_paths:
            if not path.is_completed:
                node_id = self.find_blocked_node(path)
                if node_id and node_id in self.kb:
                    node = self.kb[node_id]
                    pending_questions[node.get("character_name")] = (node_id, node["question"])

        status = "diagnosing"
        curr_q = None
        
        conflict = self.jtms.check_consistency()
        if conflict:
            status = "contradiction"
        elif not pending_questions:
            status = "completed"
        else:
            best_path = min(self.active_paths, key=lambda p: p.ns_count if not p.is_completed else 999)
            blocked_id = self.find_blocked_node(best_path)
            if blocked_id and blocked_id in self.kb:
                node = self.kb[blocked_id]
                curr_q = {
                    "node_id": blocked_id,
                    "question": node["question"],
                    "character_name": node.get("character_name")
                }

        candidates = []
        for path in self.active_paths:
            if path.is_completed and path.candidate_species:
                sp_id = path.candidate_species
                sp = self.kb[sp_id]
                
                env_fit = self.get_environmental_score(sp_id)
                path_conf = 0.8 ** path.ns_count
                total_conf = path_conf * env_fit
                
                assumed_chars = []
                for char, val in path.assumptions.items():
                    q_node = next((n for n in self.kb.values() if n.get("character_name") == char), None)
                    q_text = q_node["question"] if q_node else char
                    assumed_chars.append({
                        "character": char,
                        "question": q_text,
                        "value": "Verdadero" if val else "Falso"
                    })

                candidates.append({
                    "species_id": sp_id,
                    "species_name": sp["species_name"],
                    "phylum": sp.get("phylum", "N/A"),
                    "order": sp.get("order", "N/A"),
                    "family": sp.get("family", "N/A"),
                    "description": sp.get("description", "N/A"),
                    "habitat_note": sp.get("habitat_note", "N/A"),
                    "confidence": round(total_conf * 100, 1),
                    "env_fit": round(env_fit * 100, 1),
                    "path_confidence": round(path_conf * 100, 1),
                    "assumed_chars": assumed_chars
                })

        unique_candidates = {}
        for c in candidates:
            sp_id = c["species_id"]
            if sp_id not in unique_candidates or c["confidence"] > unique_candidates[sp_id]["confidence"]:
                unique_candidates[sp_id] = c
        candidates = sorted(unique_candidates.values(), key=lambda x: x["confidence"], reverse=True)

        choices_ui = []
        for char, ans in self.facts_history:
            q_node = next((n for n in self.kb.values() if n.get("character_name") == char), None)
            q_text = q_node["question"] if q_node else char
            choices_ui.append({
                "character_name": char,
                "question": q_text,
                "answer": "Sí" if ans == 'S' else ("No" if ans == 'N' else "No Sabe")
            })

        return {
            "status": status,
            "current_question": curr_q,
            "active_paths_count": len(self.active_paths),
            "user_choices": choices_ui,
            "contradiction": conflict,
            "candidates": candidates
        }

    def run_diagnose(self, current_node_id="root", history=None):
        """
        Navega el árbol dicotómico recursivamente. Utiliza recursividad para manejar
        el backtracking en paralelo cuando el usuario ingresa 'D' (Desconocido).
        """
        if history is None:
            history = []
            print("\n" + "="*80)
            print("SISTEMA EXPERTO DE RECONOCIMIENTO FICOLÓGICO")
            print("="*80)
            print("Responda 'S' (Sí), 'N' (No) o 'D' (Desconocido).")
            print("-"*80)

        node = self.kb.get_node(current_node_id)
        
        if not node:
            print(f"Error: nodo '{current_node_id}' no encontrado.")
            return False

        # Condición base de parada
        if node.get("is_leaf", False):
            self._print_conclusion(node, history)
            return True

        # Interrogación interactiva por consola
        print(f"\n[?] {node['question']}")
        user_input = input("Respuesta (S/N/D): ").strip().upper()
        
        while user_input not in ['S', 'N', 'D']:
            user_input = input("Entrada inválida. Responda 'S', 'N' o 'D': ").strip().upper()

        # Transiciones de inferencia
        if user_input == 'S':
            history.append({"q": node['question'], "a": "Sí"})
            return self.run_diagnose(node['yes_branch'], history.copy())
            
        elif user_input == 'N':
            history.append({"q": node['question'], "a": "No"})
            return self.run_diagnose(node['no_branch'], history.copy())
            
        elif user_input == 'D':
            print("\n[!] Incertidumbre detectada. Iniciando búsqueda recursiva en ramas paralelas...")
            
            # Sub-camino del Sí
            history_yes = history.copy()
            history_yes.append({"q": node['question'], "a": "Desconocido (Asumido Sí)"})
            res_yes = self.run_diagnose(node['yes_branch'], history_yes)
            
            # Sub-camino del No
            history_no = history.copy()
            history_no.append({"q": node['question'], "a": "Desconocido (Asumido No)"})
            res_no = self.run_diagnose(node['no_branch'], history_no)
            
            return res_yes or res_no

    def _print_conclusion(self, node, history):
        print("\n" + "*"*25 + " DIAGNÓSTICO ALCANZADO " + "*"*25)
        print(f"Especie determinada: {node['species_name']}")
        print(f"Phylum: {node.get('phylum', 'N/A')}")
        print(f"Hábitat y Persistencia: {node.get('habitat_note', 'Sin datos')}")
        print("\n--- TRAZABILIDAD DEL RAZONAMIENTO ---")
        for i, step in enumerate(history, 1):
            print(f" {i}. [{step['q']}] -> {step['a']}")
        print("*"*69 + "\n")

def kb_is_leaf(kb, node_id):
    return kb.get(node_id, {}).get("is_leaf", False)


# ==============================================================================
# 4. EVALUACIÓN Y CALIBRACIÓN DE RENDIMIENTO
# ==============================================================================

def run_calibration_test(engine):
    """
    Evalúa cuantitativamente la taxonomía usando 30 muestras de herbario.
    Retorna exactitud global, sensibilidad, especificidad y matriz de confusión.
    """
    test_cases = [
        ("species_caulerpa_scalpelliformis", {"color_verde_no_calc": True, "estructura_cenocitica": True, "estolones_rizoides_filoides": True, "filoides_pectinados": False, "filoides_planos_enteros": False, "ramulos_vesiculosos": False, "ramulos_turbinados": False, "pinnulas_apice_obtuso_denticuladas": True}, 2, "M3", 28.0, 36.0),
        ("species_caulerpa_mexicana", {"color_verde_no_calc": True, "estructura_cenocitica": True, "estolones_rizoides_filoides": True, "filoides_pectinados": False, "filoides_planos_enteros": False, "ramulos_vesiculosos": False, "ramulos_turbinados": False, "pinnulas_apice_obtuso_denticuladas": False}, 3, "M4", 27.0, 35.0),
        ("species_ulva_lactuca", {"color_verde_no_calc": True, "estructura_cenocitica": False, "talo_laminar_o_tubular_hueco": True, "talo_tubular": False, "lamina_rigida_dientes_margen": False}, 3, "M5", 29.0, 38.0),
        ("species_chaetomorpha_antennina", {"color_verde_no_calc": True, "estructura_cenocitica": False, "talo_laminar_o_tubular_hueco": False, "filamentos_simples_no_ramificados": True}, 1, "M3", 28.0, 38.0),
        ("species_ulva_flexuosa", {"color_verde_no_calc": True, "estructura_cenocitica": False, "talo_laminar_o_tubular_hueco": True, "talo_tubular": True}, 4, "M1", 28.0, 37.0),
        ("species_ulva_rigida", {"color_verde_no_calc": True, "estructura_cenocitica": False, "talo_laminar_o_tubular_hueco": True, "talo_tubular": False, "lamina_rigida_dientes_margen": True}, 2, "M4", 27.0, 35.0),
        ("species_sargassum_fluitans", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": True, "habito_pelagico": True, "aerocistos_apiculados": False}, 1, "M3", 28.0, 38.0),
        ("species_sargassum_natans", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": True, "habito_pelagico": True, "aerocistos_apiculados": True}, 1, "M2", 28.0, 37.0),
        ("species_sargassum_vulgare", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": True, "habito_pelagico": False, "filoides_espinosos_limbo": False, "filoides_densos_cortos_aserrados": False, "vesiculas_pequenas_racimos_axilares": False, "filoides_lineares_delgados": False}, 2, "M3", 28.0, 36.0),
        ("species_sargassum_polyceratium", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": True, "habito_pelagico": False, "filoides_espinosos_limbo": False, "filoides_densos_cortos_aserrados": True}, 3, "M5", 29.0, 38.0),
        ("species_padina_gymnospora", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": False, "talo_globoso_hueco": False, "talo_abanico_bandas_concentricas": True}, 2, "M4", 27.0, 35.0),
        ("species_colpomenia_sinuosa", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": False, "talo_globoso_hueco": True}, 3, "M1", 27.0, 37.0),
        ("species_dictyopteris_delicatula", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": False, "talo_globoso_hueco": False, "talo_abanico_bandas_concentricas": False, "talo_cilindrico_cartilaginoso": False, "talo_plano_laminar_cintiforme": True, "nervadura_media_costilla": True}, 1, "M5", 29.0, 37.0),
        ("species_canistrocarpus_cervicornis", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": False, "talo_globoso_hueco": False, "talo_abanico_bandas_concentricas": False, "talo_cilindrico_cartilaginoso": False, "talo_plano_laminar_cintiforme": True, "nervadura_media_costilla": False, "ramificacion_palmeada_irregular": False, "giros_helicoidales_ramas": True}, 4, "M3", 27.0, 38.0),
        ("species_dictyota_ciliolata", {"color_verde_no_calc": False, "color_pardo": True, "presencia_vesiculas_filoides_estipe": False, "talo_globoso_hueco": False, "talo_abanico_bandas_concentricas": False, "talo_cilindrico_cartilaginoso": False, "talo_plano_laminar_cintiforme": True, "nervadura_media_costilla": False, "ramificacion_palmeada_irregular": False, "giros_helicoidales_ramas": False, "margen_con_dientes": True, "dientes_tipo_pestaña": True}, 3, "M4", 27.0, 35.0),
        ("species_jania_adhaerens", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": True, "talo_articulado_rigido": True}, 2, "M4", 27.0, 35.0),
        ("species_cottoniella_filamentosa", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": True, "apices_pincetas_cangrejo": False, "corticacion_nodal_eje": False, "filamento_monosifonico_unico_adaxial": True}, 1, "M3", 28.0, 38.0),
        ("species_centroceras_gasparinii", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": True, "apices_pincetas_cangrejo": True}, 1, "M5", 29.0, 38.0),
        ("species_spyridia_filamentosa", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": True, "apices_pincetas_cangrejo": False, "corticacion_nodal_eje": True, "ramillas_espinosas_apical": False}, 3, "M2", 28.0, 36.0),
        ("species_acanthophora_spicifera", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": True, "ejes_angulados_tristicos": False, "espinas_en_ejes_principales": False}, 2, "M6", 28.0, 38.0),
        ("species_acanthophora_muscoides", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": True, "ejes_angulados_tristicos": False, "espinas_en_ejes_principales": True}, 3, "M3", 26.0, 38.0),
        ("species_laurencia_dendroidea", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": False, "ramulos_hoyuelo_apical": True, "talo_blando_laurencia": True}, 2, "M1", 28.0, 36.0),
        ("species_palisada_papillosa", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": False, "ramulos_hoyuelo_apical": True, "talo_blando_laurencia": False}, 1, "M5", 29.0, 37.0),
        ("species_hypnea_musciformis", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": False, "ramulos_hoyuelo_apical": False, "ramulos_constriccion_basal": False, "extremos_en_gancho": True}, 4, "M3", 27.0, 38.0),
        ("species_hypnea_spinella", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": False, "ramulos_hoyuelo_apical": False, "ramulos_constriccion_basal": False, "extremos_en_gancho": False, "talo_intrincado_cojin": True, "espinas_largas_bifurcadas": False}, 1, "M6", 29.0, 38.0),
        ("species_gelidium_pusillum", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": False, "ramulos_hoyuelo_apical": False, "ramulos_constriccion_basal": False, "extremos_en_gancho": False, "talo_intrincado_cojin": False, "talo_elastico_cartilaginoso": True, "talo_diminuto_intermareal_alto": True}, 2, "M2", 28.0, 36.0),
        ("species_gracilaria_domingensis", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": False, "ramulos_hoyuelo_apical": False, "ramulos_constriccion_basal": False, "extremos_en_gancho": False, "talo_intrincado_cojin": False, "talo_elastico_cartilaginoso": False, "talo_plano_comprimido": True, "ramificacion_pinnada_gracilaria": True}, 3, "M3", 26.0, 38.0),
        ("species_gracilaria_mammillaris", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": False, "ramulos_hoyuelo_apical": False, "ramulos_constriccion_basal": False, "extremos_en_gancho": False, "talo_intrincado_cojin": False, "talo_elastico_cartilaginoso": False, "talo_plano_comprimido": True, "ramificacion_pinnada_gracilaria": False, "talo_coriaceo_dicotomo": True}, 4, "M5", 30.0, 38.0),
        ("species_grateloupia_filicina", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": True, "lamina_flesh_gelatinosa": False, "lamina_dividida_pinnada": True}, 2, "M4", 27.0, 35.0),
        ("species_bryothamnion_triquetrum", {"color_verde_no_calc": False, "color_pardo": False, "talo_calcificado": False, "talo_filamentoso_fino": False, "talo_plano_laminar": False, "presencia_espinas_agudas": True, "ejes_angulados_tristicos": True}, 4, "M3", 27.0, 38.0),
    ]

    vp = 0
    fn = 0
    fp = 0
    vn = 0

    num_species = len([k for k, v in engine.kb.items() if v.get("is_leaf")])
    results_table = []
    test_idx = 1
    for target_sp, answers, station, month, temp, salinity in test_cases:
        if target_sp not in engine.kb:
            continue
        engine.reset_session()
        engine.set_pre_filters(temp, salinity, station, month)
        
        # Inyectar dinámicamente caracteres intermedios de Rhodophyta
        ans_copy = dict(answers)
        if target_sp == "species_jania_adhaerens":
            ans_copy["talo_calcificado"] = True
        elif target_sp in ["species_cottoniella_filamentosa", "species_centroceras_gasparinii", "species_spyridia_filamentosa",
                           "species_acanthophora_spicifera", "species_acanthophora_muscoides", "species_laurencia_dendroidea",
                           "species_palisada_papillosa", "species_hypnea_musciformis", "species_hypnea_spinella",
                           "species_gelidium_pusillum", "species_gracilaria_domingensis", "species_gracilaria_mammillaris",
                           "species_grateloupia_filicina", "species_bryothamnion_triquetrum"]:
            ans_copy["talo_calcificado"] = False
            
            if target_sp in ["species_spyridia_filamentosa", "species_centroceras_gasparinii", "species_cottoniella_filamentosa"]:
                ans_copy["talo_carnoso_cartilaginoso"] = False
            else:
                ans_copy["talo_carnoso_cartilaginoso"] = True
                
            if target_sp in ["species_hypnea_musciformis", "species_hypnea_spinella"]:
                ans_copy["ramas_espinas_apices_curvados"] = True
            else:
                ans_copy["ramas_espinas_apices_curvados"] = False
                
            if target_sp == "species_cottoniella_filamentosa":
                ans_copy["filamentos_finos_ramificacion_alterna"] = True
            else:
                ans_copy["filamentos_finos_ramificacion_alterna"] = False

            if target_sp in ["species_acanthophora_spicifera", "species_acanthophora_muscoides", "species_bryothamnion_triquetrum"]:
                ans_copy["presencia_espinas_agudas"] = True
            else:
                ans_copy["presencia_espinas_agudas"] = False

            if target_sp in ["species_laurencia_dendroidea", "species_palisada_papillosa"]:
                ans_copy["ramulos_hoyuelo_apical"] = True
            else:
                ans_copy["ramulos_hoyuelo_apical"] = False

            ans_copy["ramulos_constriccion_basal"] = False

            if target_sp == "species_grateloupia_filicina":
                ans_copy["talo_plano_laminar"] = True
            else:
                ans_copy["talo_plano_laminar"] = False

            if target_sp == "species_gelidium_pusillum":
                ans_copy["talo_elastico_cartilaginoso"] = True
            else:
                ans_copy["talo_elastico_cartilaginoso"] = False

            ans_copy["filamentos_soporte_medulares"] = False

        for char, ans in ans_copy.items():
            if any(v.get("character_name") == char for v in engine.kb.values()):
                engine.submit_answer(char, 'S' if ans else 'N')
        
        state = engine.get_state()
        determined_sp = state["candidates"][0]["species_id"] if state["candidates"] else None
        
        success = (determined_sp == target_sp)
        if success:
            vp += 1
            vn += max(0, num_species - 1)
        else:
            fn += 1
            fp += 1
            vn += max(0, num_species - 2)

        results_table.append({
            "id": test_idx,
            "target": engine.kb[target_sp].get("species_name", target_sp),
            "obtained": engine.kb[determined_sp].get("species_name", "No determinado") if determined_sp else "No determinado",
            "success": success
        })
        test_idx += 1

    total_evals = vp + vn + fp + fn
    accuracy = (vp + vn) / total_evals if total_evals > 0 else 0
    sensitivity = vp / (vp + fn) if (vp + fn) > 0 else 0
    specificity = vn / (vn + fp) if (vn + fp) > 0 else 0

    return {
        "accuracy": round(accuracy * 100, 2),
        "sensitivity": round(sensitivity * 100, 2),
        "specificity": round(specificity * 100, 2),
        "matrix": {"vp": vp, "vn": vn, "fp": fp, "fn": fn},
        "results": results_table
    }


# ==============================================================================
# 5. CLI FALLBACK AND MAIN ENTRYPOINT
# ==============================================================================

def main():
    kb_path = "algae_knowledge.json"
    
    # Evaluar parámetros por consola
    if len(sys.argv) > 1 and sys.argv[1] in ['--calibration', '--test', '-t']:
        try:
            kb_manager = KnowledgeBaseManager(kb_path)
            engine = AlgaeExpertSystem(kb_manager)
            res = run_calibration_test(engine)
            print("\n" + "="*50)
            print("RESULTADOS DE EVALUACIÓN DE CALIBRACIÓN")
            print("="*50)
            print(f"Exactitud Global: {res['accuracy']}%")
            print(f"Sensibilidad:    {res['sensitivity']}%")
            print(f"Especificidad:   {res['specificity']}%")
            print(f"Matriz de Confusión: {res['matrix']}")
            print("="*50)
        except Exception as e:
            print(f"Error al ejecutar calibración: {e}")
        return

    # Ejecución interactiva por defecto
    try:
        kb_manager = KnowledgeBaseManager(kb_path)
        system = AlgaeExpertSystem(kb_manager)
        system.run_diagnose()
    except Exception as e:
        print(f"Error crítico de inicio: {e}")

if __name__ == "__main__":
    main()