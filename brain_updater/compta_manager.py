"""Module Comptable & Fiscal Micro-Entreprise BNC pour Apify Store.

Spécialiste de la fiscalité française des créateurs de logiciels et 'Actors' Apify:
- Gestion des encaissements en devises (USD convertis en EUR au cours réel).
- Facturation B2B intracommunautaire (Apify Technologies s.r.o., Prague, CZ).
- Autoliquidation de TVA (Art. 283-1 CGI & Art. 196 Directive 2006/112/CE).
- Suivi du seuil de Franchise en Base de TVA (36 800 € / 39 100 €).
- Suivi du Plafond Micro-BNC (77 700 €).
- Calcul des cotisations URSSAF (21.1% + CFP 0.2% = 21.3%, et régime ACRE).
- Cases fiscales officielles pour la déclaration d'impôt 2042-C-PRO (Case 5HQ ou 5TE).
- Génération du tableau de bord interactif HTML (tableau_de_bord_fiscal.html).
"""

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "compta_impots" / "livre_des_recettes_bnc.csv"
HTML_DASHBOARD_PATH = REPO_ROOT / "compta_impots" / "tableau_de_bord_fiscal.html"

# Plafonds fiscaux officiels Micro-BNC
PLAFOND_MICRO_BNC = 77700.00
SEUIL_BASE_TVA = 36800.00
SEUIL_MAJORE_TVA = 39100.00

# Taux officiels URSSAF Micro-BNC (Prestation de services / Professions libérales non réglementées)
TAUX_URSSAF_STANDARD = 0.211  # Cotisations sociales 21.1%
TAUX_CFP = 0.002             # Contribution Formation Professionnelle 0.2%
TAUX_TOTAL_URSSAF = TAUX_URSSAF_STANDARD + TAUX_CFP  # 21.3%
TAUX_ACRE = 0.1065            # Taux réduit première année (50% d'exonération)
TAUX_VERSEMENT_LIBERATOIRE = 0.022  # 2.2% en BNC si éligible


def load_recettes_csv() -> List[Dict[str, Any]]:
    """Charger les encaissements depuis le livre de recettes officiel."""
    if not CSV_PATH.exists():
        print(f"[-] Fichier non trouvé : {CSV_PATH}")
        return []

    recettes = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                row["montant_ht_eur"] = float(row.get("montant_ht_eur", 0) or 0)
                row["tva_montant"] = float(row.get("tva_montant", 0) or 0)
                row["montant_ttc_eur"] = float(row.get("montant_ttc_eur", 0) or 0)
                recettes.append(row)
            except ValueError:
                continue
    return recettes


def compute_financial_kpis(recettes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculer tous les indicateurs comptables et fiscaux."""
    total_ht = sum(r["montant_ht_eur"] for r in recettes)
    total_ttc = sum(r["montant_ttc_eur"] for r in recettes)

    # Calcul URSSAF
    cotisations_standard = round(total_ht * TAUX_TOTAL_URSSAF, 2)
    cotisations_acre = round(total_ht * (TAUX_ACRE + TAUX_CFP), 2)
    versement_liberatoire = round(total_ht * TAUX_VERSEMENT_LIBERATOIRE, 2)

    # Déclaration Impôt sur le Revenu (2042-C-PRO)
    # Case 5HQ : Sans versement libératoire (l'État applique 34% d'abattement)
    abattement_forfaitaire_34 = round(total_ht * 0.34, 2)
    revenu_net_imposable_5hq = round(total_ht * 0.66, 2)

    # Case 5TE : Si option versement libératoire
    base_5te = round(total_ht, 2)

    # Pourcentages des plafonds
    pct_plafond_bnc = round((total_ht / PLAFOND_MICRO_BNC) * 100, 1)
    pct_seuil_tva = round((total_ht / SEUIL_BASE_TVA) * 100, 1)

    # Alertes
    franchise_depassee = total_ht > SEUIL_BASE_TVA
    seuil_majore_depasse = total_ht > SEUIL_MAJORE_TVA
    plafond_bnc_depasse = total_ht > PLAFOND_MICRO_BNC

    return {
        "total_ht": round(total_ht, 2),
        "total_ttc": round(total_ttc, 2),
        "nombre_encaissements": len(recettes),
        "cotisations_urssaf_standard": cotisations_standard,
        "cotisations_urssaf_acre": cotisations_acre,
        "versement_liberatoire_ir": versement_liberatoire,
        "abattement_forfaitaire_34": abattement_forfaitaire_34,
        "revenu_net_imposable_5hq": revenu_net_imposable_5hq,
        "base_declaration_5te": base_5te,
        "pct_plafond_bnc": pct_plafond_bnc,
        "pct_seuil_tva": pct_seuil_tva,
        "franchise_depassee": franchise_depassee,
        "seuil_majore_depasse": seuil_majore_depasse,
        "plafond_bnc_depasse": plafond_bnc_depasse,
    }


def generate_html_dashboard(recettes: List[Dict[str, Any]], kpis: Dict[str, Any]) -> None:
    """Générer le tableau de bord fiscal moderne et autonome en HTML."""
    rows_html = []
    for r in recettes:
        rows_html.append(f"""
        <tr>
          <td><strong>{r.get('date_encaissement')}</strong></td>
          <td><span class="badge badge-light">{r.get('reference_piece')}</span></td>
          <td>{r.get('client_nom')}<br><small class="text-muted">{r.get('pays_client')}</small></td>
          <td>{r.get('nature_prestation')}</td>
          <td class="text-end font-monospace"><strong>{r.get('montant_ht_eur'):.2f} €</strong></td>
          <td class="text-center"><span class="badge badge-success">Autoliquidation 0%</span></td>
          <td class="text-end font-monospace">{r.get('mode_reglement')}</td>
          <td><code>{r.get('reference_virement_apify')}</code></td>
        </tr>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tableau de Bord Fiscal Micro-Entreprise BNC — Apify Store</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <style>
    body {{ background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    .card-kpi {{ border-radius: 12px; border: none; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .kpi-title {{ font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; color: #64748b; }}
    .kpi-value {{ font-size: 1.85rem; font-weight: 700; color: #0f172a; }}
    .progress {{ height: 10px; border-radius: 6px; }}
    .badge-success {{ background-color: #dcfce7; color: #15803d; }}
    .badge-light {{ background-color: #f1f5f9; color: #334155; }}
    .rule-card {{ border-left: 4px solid #3b82f6; }}
    .rule-card-warning {{ border-left: 4px solid #f59e0b; }}
  </style>
</head>
<body class="py-4">
  <div class="container-xl">
    
    <!-- En-tête -->
    <div class="d-flex justify-content-between align-items-center mb-4 pb-3 border-bottom">
      <div>
        <h2 class="fw-bold mb-1"><i class="fa-solid fa-scale-balanced text-primary me-2"></i>Tableau de Bord Fiscal Micro-BNC</h2>
        <p class="text-muted mb-0">Gestion comptable certifiée pour revenus Apify Store & Développeur Freelance BNC</p>
      </div>
      <div class="text-end">
        <span class="badge bg-primary px-3 py-2 fs-6">Exercice Fiscal 2026</span>
        <button onclick="window.print()" class="btn btn-outline-secondary btn-sm ms-2"><i class="fa-solid fa-print me-1"></i>Imprimer</button>
      </div>
    </div>

    <!-- Alertes Statut -->
    <div class="row g-3 mb-4">
      <div class="col-md-3">
        <div class="card card-kpi p-3">
          <div class="kpi-title">CA Total Encaissé (HT)</div>
          <div class="kpi-value">{kpis['total_ht']:.2f} €</div>
          <small class="text-muted">{kpis['nombre_encaissements']} encaissements comptabilisés</small>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card card-kpi p-3">
          <div class="kpi-title">Plafond Micro-BNC (77 700 €)</div>
          <div class="kpi-value">{kpis['pct_plafond_bnc']}%</div>
          <div class="progress mt-2">
            <div class="progress-bar bg-info" style="width: {min(100, kpis['pct_plafond_bnc'])}%"></div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card card-kpi p-3">
          <div class="kpi-title">Franchise TVA (36 800 €)</div>
          <div class="kpi-value">{kpis['pct_seuil_tva']}%</div>
          <div class="progress mt-2">
            <div class="progress-bar {'bg-success' if not kpis['franchise_depassee'] else 'bg-danger'}" style="width: {min(100, kpis['pct_seuil_tva'])}%"></div>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card card-kpi p-3">
          <div class="kpi-title">Cotisations URSSAF (21.3%)</div>
          <div class="kpi-value text-primary">{kpis['cotisations_urssaf_standard']:.2f} €</div>
          <small class="text-muted">(Avec ACRE : {kpis['cotisations_urssaf_acre']:.2f} €)</small>
        </div>
      </div>
    </div>

    <!-- Déclarations Fiscales Officielles -->
    <div class="card card-kpi p-4 mb-4">
      <h5 class="fw-bold mb-3"><i class="fa-solid fa-file-invoice-dollar me-2 text-warning"></i>Guide de Report Déclaratif Officiel</h5>
      <div class="row g-4">
        <div class="col-md-6">
          <div class="p-3 bg-light rounded border">
            <h6 class="fw-bold text-primary mb-2">Option 1 : Régime Micro-BNC Standard (Case 5HQ)</h6>
            <p class="small text-muted mb-2">Si vous n'avez <strong>pas</strong> opté pour le versement libératoire de l'IR :</p>
            <ul class="small mb-2">
              <li>Déclarer sur la <strong>2042-C-PRO</strong> dans la case <strong>5HQ</strong> : <strong>{kpis['total_ht']:.2f} €</strong></li>
              <li>L'Administration applique automatiquement un abattement forfaitaire de <strong>34%</strong> (-{kpis['abattement_forfaitaire_34']:.2f} €)</li>
              <li>Votre revenu net professionnel imposable est de : <strong>{kpis['revenu_net_imposable_5hq']:.2f} €</strong></li>
            </ul>
          </div>
        </div>
        <div class="col-md-6">
          <div class="p-3 bg-light rounded border">
            <h6 class="fw-bold text-success mb-2">Option 2 : Avec Versement Libératoire (Case 5TE)</h6>
            <p class="small text-muted mb-2">Si vous avez activé le versement libératoire de l'IR (taux BNC : 2.2%) :</p>
            <ul class="small mb-2">
              <li>Montant d'impôt libératoire déjà réglé à l'URSSAF : <strong>{kpis['versement_liberatoire_ir']:.2f} €</strong></li>
              <li>Déclarer sur la <strong>2042-C-PRO</strong> dans la case <strong>5TE</strong> : <strong>{kpis['total_ht']:.2f} €</strong></li>
              <li>Ce montant est non imposable au barème progressif (pris en compte uniquement pour le TMI global).</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Règles Juridiques & TVA Apify -->
    <div class="row g-4 mb-4">
      <div class="col-md-6">
        <div class="card card-kpi p-3 rule-card h-100">
          <h6 class="fw-bold text-dark mb-2"><i class="fa-solid fa-globe me-2 text-primary"></i>Territorialité & TVA Apify Technologies s.r.o.</h6>
          <p class="small text-muted mb-2">
            Apify est une société basée à Prague (République Tchèque, UE) titulaire du numéro de TVA <strong>CZ04970550</strong>.
          </p>
          <ul class="small mb-0">
            <li>Conformément à l'<strong>Article 259-1 du CGI</strong>, la prestation est réputée située dans le pays du preneur.</li>
            <li>La facture est obligatoirement émise <strong>Hors Taxe (TVA à 0%)</strong> avec la mention :<br>
              <em class="text-dark">« Autoliquidation de la TVA - Article 283-1 du CGI et Article 196 de la Directive 2006/112/CE »</em>.
            </li>
          </ul>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card card-kpi p-3 rule-card-warning h-100">
          <h6 class="fw-bold text-dark mb-2"><i class="fa-solid fa-passport me-2 text-warning"></i>Obligation Douanière : Déclaration DES</h6>
          <p class="small text-muted mb-2">
            Toute prestation B2B de services intracommunautaire impose le dépôt d'une <strong>Déclaration Européenne de Services (DES)</strong>.
          </p>
          <ul class="small mb-0">
            <li>À télédéclarer sur le portail des douanes (<code>douane.gouv.fr</code>) avant le 10 du mois suivant chaque encaissement.</li>
            <li>Renseigner le numéro de TVA intracommunautaire d'Apify (<code>CZ04970550</code>).</li>
            <li>Amende de 15 € par omission si omis.</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Livre des Recettes BNC -->
    <div class="card card-kpi p-4">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="fw-bold mb-0"><i class="fa-solid fa-list-check me-2 text-primary"></i>Livre des Recettes Chronologique BNC</h5>
        <span class="text-muted small">Conforme à l'article 99 du Code Général des Impôts</span>
      </div>
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>Date</th>
              <th>Réf. Pièce</th>
              <th>Client</th>
              <th>Nature de la Prestation</th>
              <th class="text-end">Montant HT</th>
              <th class="text-center">TVA</th>
              <th class="text-end">Règlement</th>
              <th>Réf. Virement</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
          <tfoot class="table-light fw-bold">
            <tr>
              <td colspan="4">TOTAL CUMULÉ DES RECETTES ENCAISSÉES</td>
              <td class="text-end font-monospace">{kpis['total_ht']:.2f} €</td>
              <td class="text-center">0.00 €</td>
              <td colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <footer class="mt-4 pt-3 text-center text-muted small border-top">
      Généré automatiquement par <code>brain_updater/compta_manager.py</code> — Apify B2B Autopilot Pack
    </footer>
  </div>
</body>
</html>
"""
    with open(HTML_DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] Tableau de bord HTML généré avec succès : {HTML_DASHBOARD_PATH}")


def main() -> None:
    """Point d'entrée du gestionnaire fiscal BNC."""
    parser = argparse.ArgumentParser(description="Gestionnaire Fiscal & Comptable Micro-BNC pour Apify Store.")
    parser.add_argument("--summary", action="store_true", help="Afficher le résumé fiscal complet en console.")
    parser.add_argument("--export-dashboard", action="store_true", help="Générer et actualiser tableau_de_bord_fiscal.html.")
    args = parser.parse_args()

    recettes = load_recettes_csv()
    kpis = compute_financial_kpis(recettes)

    if args.summary or len(sys.argv) == 1:
        print("\n==================================================================")
        print("   ⚖️  SYNTHÈSE COMPTABLE & FISCALE MICRO-BNC (APIFY STORE)")
        print("==================================================================")
        print(f"Total Chiffre d'Affaires Encaissé : {kpis['total_ht']:.2f} €")
        print(f"Nombre d'encaissements : {kpis['nombre_encaissements']}")
        print(f"Plafond Micro-BNC (77 700 €) : {kpis['pct_plafond_bnc']}% utilisé")
        print(f"Seuil de Franchise TVA (36 800 €) : {kpis['pct_seuil_tva']}% utilisé")
        print("------------------------------------------------------------------")
        print(f"Cotisations URSSAF (21.3%) : {kpis['cotisations_urssaf_standard']:.2f} €")
        print(f"Cotisations avec ACRE (10.85%) : {kpis['cotisations_urssaf_acre']:.2f} €")
        print("------------------------------------------------------------------")
        print("📋 DÉCLARATION D'IMPÔT SUR LE REVENU 2042-C-PRO :")
        print(f"  -> Sans versement libératoire (Case 5HQ) : {kpis['total_ht']:.2f} €")
        print(f"     (Revenu net imposable après abattement 34% : {kpis['revenu_net_imposable_5hq']:.2f} €)")
        print(f"  -> Avec versement libératoire (Case 5TE) : {kpis['base_declaration_5te']:.2f} €")
        print(f"     (Montant versement libératoire 2.2% : {kpis['versement_liberatoire_ir']:.2f} €)")
        print("==================================================================\n")

    generate_html_dashboard(recettes, kpis)


if __name__ == "__main__":
    main()
