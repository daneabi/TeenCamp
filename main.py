import json
import os
import random

FILE_NAME = 'roster_v2.json'

CHORES = [
    {"navn": "Morgenmad Køkken", "ledere": 1, "teens": 3, "køn_krav": None},
    {"navn": "Morgenmad Opvask + Spisestuen", "ledere": 1, "teens": 3, "køn_krav": None},
    {"navn": "Frokost Køkken", "ledere": 2, "teens": 3, "køn_krav": None},
    {"navn": "Frokost Opvask + Spisestuen", "ledere": 1, "teens": 3, "køn_krav": None},
    {"navn": "Aftensmad Køkkenet", "ledere": 2, "teens": 3, "køn_krav": None},
    {"navn": "Aftensmad Opvask + Spisestuen", "ledere": 1, "teens": 3, "køn_krav": None},
    {"navn": "Toilet: Piger", "ledere": 1, "teens": 2, "køn_krav": "F"},
    {"navn": "Toilet: Drenge", "ledere": 1, "teens": 2, "køn_krav": "M"},
]

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {"teenagers": [], "leaders": []}

def save_data(data):
    with open(FILE_NAME, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def get_next_person(available_pool, full_list, arbejder_i_dag, køn=None):
    """Trækker den næste person, med prioritet på at de ikke har arbejdet i dag."""
    if not full_list:
        return {"navn": "[INGEN I LISTEN]", "køn": "?"}

    # Sikkerhedstjek: Findes kønnet overhovedet?
    if køn and not any(p['køn'] == køn for p in full_list):
        return {"navn": f"[MANGLER {køn}]", "køn": køn}

    # Fyld puljen hvis den er tom
    if not available_pool:
        available_pool.extend(random.sample(full_list, len(full_list)))

    # 1. Prioritet: Find en i puljen der matcher køn OG ikke arbejder i dag
    gyldige_i_pulje = [p for p in available_pool if (køn is None or p['køn'] == køn) and p['navn'] not in arbejder_i_dag]
    
    if gyldige_i_pulje:
        valgt = gyldige_i_pulje[0]
        available_pool.remove(valgt)
        arbejder_i_dag.add(valgt['navn'])
        return valgt

    # 2. Prioritet: Træk "midlertidigt" fra den fulde liste, men KUN en der IKKE arbejder i dag
    ekstra_kandidater = [p for p in full_list if (køn is None or p['køn'] == køn) and p['navn'] not in arbejder_i_dag]
    
    if ekstra_kandidater:
        valgt = random.choice(ekstra_kandidater)
        # Hvis de var i bunden af the available_pool pga. andre filtreringer, fjern dem derfra også
        if valgt in available_pool:
            available_pool.remove(valgt)
            
        arbejder_i_dag.add(valgt['navn'])
        return valgt

    # 3. Fallback (Sker kun hvis I er underbemandede): Alle af dette køn arbejder ALLEREDE i dag.
    # Vi er nødt til at tildele en person en ekstra tjans på samme dag.
    fallback_pulje = [p for p in available_pool if (køn is None or p['køn'] == køn)]
    if fallback_pulje:
        valgt = fallback_pulje[0]
        available_pool.remove(valgt)
    else:
        alle_af_køn = [p for p in full_list if (køn is None or p['køn'] == køn)]
        valgt = random.choice(alle_af_køn)

    arbejder_i_dag.add(valgt['navn'])
    return valgt

def generate_daily_schedule(data):
    available_teens = []
    available_leaders = []
    
    available_teens.extend(random.sample(data['teenagers'], len(data['teenagers'])))
    available_leaders.extend(random.sample(data['leaders'], len(data['leaders'])))

    try:
        dage = int(input("Hvor mange dage vil du generere en plan for? "))
    except ValueError:
        print("Ugyldigt antal dage. Går tilbage til menuen.")
        return
    
    for dag in range(1, dage + 1):
        print(f"\n================ DAG {dag} ================")
        
        # Nulstil hvem der har fået en opgave for den nye dag
        arbejder_i_dag_ledere = set()
        arbejder_i_dag_teens = set()
        
        for chore in CHORES:
            tildelte_ledere = []
            tildelte_teens = []
            
            for _ in range(chore['ledere']):
                person = get_next_person(available_leaders, data['leaders'], arbejder_i_dag_ledere, chore['køn_krav'])
                tildelte_ledere.append(person['navn'])
                
            for _ in range(chore['teens']):
                person = get_next_person(available_teens, data['teenagers'], arbejder_i_dag_teens, chore['køn_krav'])
                tildelte_teens.append(person['navn'])
                
            print(f"\n[{chore['navn']}]")
            print(f"  Ledere : {', '.join(tildelte_ledere)}")
            print(f"  Teens  : {', '.join(tildelte_teens)}")
        print("=========================================")

def main():
    data = load_data()

    while True:
        print("\n--- Lejr Opgave Fordeler ---")
        print("1. Tilføj Teenager(s)")
        print("2. Tilføj Leder(e)")
        print("3. Generer Plan for X dage")
        print("4. Ryd lister")
        print("5. Afslut")
        
        choice = input("Vælg (1-5): ")

        if choice == '1' or choice == '2':
            rolle = "teenagers" if choice == '1' else "leaders"
            print(f"\n--- Tilføjer til {rolle} ---")
            print("(Tryk bare Enter uden at skrive et navn, når du er færdig)")
            
            tilføjet_antal = 0
            while True:
                navn = input("\nIndtast navn (eller tryk Enter for at stoppe): ").strip()
                
                # Hvis brugeren ikke skriver noget, afbryder vi loopet
                if not navn:
                    break
                
                køn = input(f"Indtast køn for {navn} (M/F): ").upper().strip()
                while køn not in ['M', 'F']:
                    køn = input("Fejl. Indtast venligst 'M' eller 'F': ").upper().strip()
                
                data[rolle].append({"navn": navn, "køn": køn})
                tilføjet_antal += 1
                print(f"  -> {navn} ({køn}) blev tilføjet.")
            
            # Vi gemmer først dataene, når vi er helt færdige med at taste ind
            if tilføjet_antal > 0:
                save_data(data)
                print(f"\nSucces! Gemte {tilføjet_antal} nye person(er) til {rolle}.")

        elif choice == '3':
            if not data['teenagers'] and not data['leaders']:
                print("Listerne er tomme! Tilføj personer først.")
            else:
                generate_daily_schedule(data)

        elif choice == '4':
            confirm = input("Er du sikker på du vil slette ALT? (y/n): ")
            if confirm.lower() == 'y':
                data = {"teenagers": [], "leaders": []}
                save_data(data)
                print("Listerne er slettet.")

        elif choice == '5':
            break

if __name__ == "__main__":
    main()