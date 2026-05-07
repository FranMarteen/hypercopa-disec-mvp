"""Analise detalhada do processo de formacao dos clusters K-Means."""
import h2o
from h2o.estimators import H2OKMeansEstimator
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

h2o.init(max_mem_size='2G', nthreads=-1)

# Preparar dados
df = pd.read_csv('./dados_sinteticos/eaps.csv')
df_conc = df[df['status'] == 'Concluído'].copy()
df_conc['log_valor'] = np.log(df_conc['valor_estimado'])
df_conc['desconto_pct'] = (
    (df_conc['valor_estimado'] - df_conc['valor_contratado'])
    / df_conc['valor_estimado'] * 100
).round(2)

features = ['log_valor', 'prazo_total_dias', 'num_participantes']
df_feat = df_conc[features].dropna().copy()

# =======================================================================
# PARTE 1: O ESPACO DE FEATURES ANTES DO CLUSTERING
# =======================================================================
print("=" * 80)
print("PARTE 1: ENTENDENDO O ESPACO DE FEATURES (antes do K-Means)")
print("=" * 80)

print("\nAs 3 dimensoes que o K-Means usa para agrupar:")
for col in features:
    s = df_feat[col]
    print(f"  {col:25s} min={s.min():>7.1f}  max={s.max():>7.1f}"
          f"  media={s.mean():>7.1f}  std={s.std():>5.1f}")

print("\nPROBLEMA DE ESCALA:")
print("  prazo_total_dias vai de 14 a 208 (range 194)")
print("  log_valor vai de 8.5 a 16.7 (range 8.2)")
print("  num_participantes vai de 1 a 17 (range 16)")
print("  Se nao normalizar, o prazo DOMINA o calculo de distancia!")
print("  Por isso usamos standardize=True no H2O.")

means = {col: df_feat[col].mean() for col in features}
stds = {col: df_feat[col].std() for col in features}

print("\nApos padronizacao (standardize=True):")
print("  Todas as features passam a ter media=0 e std=1")
print("  Agora cada dimensao pesa igualmente no calculo de distancia")

# =======================================================================
# PARTE 2: CONVERGENCIA DO ALGORITMO
# =======================================================================
print("\n" + "=" * 80)
print("PARTE 2: O ALGORITMO K-MEANS PASSO A PASSO")
print("=" * 80)

hf = h2o.H2OFrame(df_feat)
iteracoes_log = []
for max_it in [1, 2, 3, 5, 10, 20, 50, 100]:
    km_it = H2OKMeansEstimator(
        k=5, standardize=True, seed=42,
        max_iterations=max_it, init="Random"
    )
    km_it.train(x=features, training_frame=hf)
    within = km_it.tot_withinss()
    between = km_it.betweenss()
    total = km_it.totss()
    iteracoes_log.append({
        'max_iter': max_it,
        'within_ss': within,
        'between_ss': between,
        'ratio': between / total
    })

print("\nConvergencia do K-Means por iteracao:")
print(f"  {'Iter':>6s}  {'Within SS':>12s}  {'Between SS':>12s}  {'Ratio':>8s}")
for r in iteracoes_log:
    print(f"  {r['max_iter']:>6d}  {r['within_ss']:>12.1f}"
          f"  {r['between_ss']:>12.1f}  {r['ratio']:>8.3f}")

print("\nO que acontece em cada iteracao:")
print("  1. Centros iniciais sao colocados aleatoriamente (seed=42)")
print("  2. Cada ponto e atribuido ao centro mais proximo (dist euclidiana)")
print("  3. Cada centro e recalculado como a media dos pontos do grupo")
print("  4. Repete 2-3 ate estabilizar")
print(f"\n  Iter 1:   ratio = {iteracoes_log[0]['ratio']:.3f} (centros ruins)")
print(f"  Iter 5:   ratio = {iteracoes_log[3]['ratio']:.3f} (ja converge)")
print(f"  Iter 100: ratio = {iteracoes_log[-1]['ratio']:.3f} (estabilizado)")

# =======================================================================
# PARTE 3: METODO DO COTOVELO
# =======================================================================
print("\n" + "=" * 80)
print("PARTE 3: POR QUE K=5 (Metodo do Cotovelo)")
print("=" * 80)

resultados_k = []
for k in range(2, 12):
    km_k = H2OKMeansEstimator(k=k, standardize=True, seed=42, max_iterations=100)
    km_k.train(x=features, training_frame=hf)
    within = km_k.tot_withinss()
    total = km_k.totss()
    resultados_k.append({
        'k': k, 'within_ss': within,
        'ratio': (total - within) / total
    })

print(f"\n  {'K':>3s}  {'Within SS':>12s}  {'Ratio':>8s}  {'Ganho marginal':>15s}")
for i, r in enumerate(resultados_k):
    ganho = ""
    if i > 0:
        g = r['ratio'] - resultados_k[i - 1]['ratio']
        ganho = f"+{g:.3f}"
        if g < 0.020:
            ganho += "  <-- pouco ganho"
    print(f"  {r['k']:>3d}  {r['within_ss']:>12.1f}  {r['ratio']:>8.3f}  {ganho}")

# =======================================================================
# PARTE 4: CENTROS FINAIS E DISTANCIAS
# =======================================================================
print("\n" + "=" * 80)
print("PARTE 4: CENTROS FINAIS (o que define cada cluster)")
print("=" * 80)

km_final = H2OKMeansEstimator(k=5, standardize=True, seed=42, max_iterations=100)
km_final.train(x=features, training_frame=hf)
centros = km_final.centers()
centros_std = km_final.centers_std()

print("\nCentros padronizados (como o K-Means ve internamente):")
print(f"  {'Cl':>3s}  {'log_valor':>10s}  {'prazo':>10s}  {'particip':>10s}")
for i, c in enumerate(centros_std):
    print(f"  {i:>3d}  {c[0]:>10.2f}  {c[1]:>10.2f}  {c[2]:>10.2f}")

print("\nCentros em valores reais (desnormalizados):")
print(f"  {'Cl':>3s}  {'log_valor':>10s}  {'~R$ equiv':>15s}"
      f"  {'prazo':>8s}  {'particip':>10s}")
for i, c in enumerate(centros):
    val = np.exp(c[0])
    print(f"  {i:>3d}  {c[0]:>10.1f}  R$ {val:>12,.0f}"
          f"  {c[1]:>8.0f}d  {c[2]:>10.1f}")

# =======================================================================
# PARTE 5: EXEMPLO DE CLASSIFICACAO
# =======================================================================
print("\n" + "=" * 80)
print("PARTE 5: EXEMPLO - COMO UM NOVO PROCESSO E CLASSIFICADO")
print("=" * 80)

ex_valor = np.log(500000)
ex_prazo = 45
ex_part = 2

print(f"\n  Novo processo: R$ 500.000 (log={ex_valor:.2f}),"
      f" prazo=45d, 2 participantes")

ex_std = [
    (ex_valor - means['log_valor']) / stds['log_valor'],
    (ex_prazo - means['prazo_total_dias']) / stds['prazo_total_dias'],
    (ex_part - means['num_participantes']) / stds['num_participantes'],
]
print(f"\n  Passo 1 - Padronizar: [{ex_std[0]:.2f}, {ex_std[1]:.2f}, {ex_std[2]:.2f}]")

print(f"\n  Passo 2 - Distancia euclidiana ate cada centro:")
dists = []
for i, c in enumerate(centros_std):
    d = np.sqrt(sum((a - b) ** 2 for a, b in zip(ex_std, c)))
    dists.append(d)
menor = np.argmin(dists)
for i, d in enumerate(dists):
    flag = "  <-- MAIS PROXIMO" if i == menor else ""
    print(f"    Dist C{i}: {d:.3f}{flag}")

print(f"\n  Passo 3 - Atribuir ao cluster mais proximo: Cluster {menor}")

# =======================================================================
# PARTE 6: GRAFICOS
# =======================================================================
pred = km_final.predict(hf)
df_feat_r = df_feat.reset_index(drop=True)
df_feat_r['cluster'] = h2o.as_list(pred)['predict'].values

colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
cl_names = [
    'C0: Licit. Grande Porte',
    'C1: Licit. Pequeno Porte',
    'C2: Direta Baixo Valor',
    'C3: Direta Alto Valor',
    'C4: Licit. Competitivas',
]

fig = plt.figure(figsize=(20, 16))
gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

# 1) Valor vs Prazo
ax1 = fig.add_subplot(gs[0, 0:2])
for cl in range(5):
    m = df_feat_r['cluster'] == cl
    ax1.scatter(df_feat_r.loc[m, 'log_valor'],
                df_feat_r.loc[m, 'prazo_total_dias'],
                c=colors[cl], alpha=0.4, s=12, label=cl_names[cl])
for i, c in enumerate(centros):
    ax1.scatter(c[0], c[1], c='black', marker='X', s=200,
                zorder=5, edgecolors='white', linewidth=2)
    ax1.annotate(f'C{i}', (c[0] + 0.1, c[1] + 3),
                 fontsize=11, fontweight='bold')
ax1.set_xlabel('log(Valor Estimado)', fontsize=12)
ax1.set_ylabel('Prazo Total (dias)', fontsize=12)
ax1.set_title('Valor x Prazo  (X = centros)', fontsize=13)
ax1.legend(fontsize=9, loc='upper left')

# 2) Valor vs Participantes
ax2 = fig.add_subplot(gs[0, 2])
for cl in range(5):
    m = df_feat_r['cluster'] == cl
    ax2.scatter(df_feat_r.loc[m, 'log_valor'],
                df_feat_r.loc[m, 'num_participantes'],
                c=colors[cl], alpha=0.4, s=12)
for i, c in enumerate(centros):
    ax2.scatter(c[0], c[2], c='black', marker='X', s=200,
                zorder=5, edgecolors='white', linewidth=2)
    ax2.annotate(f'C{i}', (c[0] + 0.1, c[2] + 0.3),
                 fontsize=11, fontweight='bold')
ax2.set_xlabel('log(Valor Estimado)', fontsize=12)
ax2.set_ylabel('Num Participantes', fontsize=12)
ax2.set_title('Valor x Participantes', fontsize=13)

# 3) Prazo vs Participantes
ax3 = fig.add_subplot(gs[1, 0])
for cl in range(5):
    m = df_feat_r['cluster'] == cl
    ax3.scatter(df_feat_r.loc[m, 'prazo_total_dias'],
                df_feat_r.loc[m, 'num_participantes'],
                c=colors[cl], alpha=0.4, s=12)
for i, c in enumerate(centros):
    ax3.scatter(c[1], c[2], c='black', marker='X', s=200,
                zorder=5, edgecolors='white', linewidth=2)
    ax3.annotate(f'C{i}', (c[1] + 2, c[2] + 0.3),
                 fontsize=11, fontweight='bold')
ax3.set_xlabel('Prazo Total (dias)', fontsize=12)
ax3.set_ylabel('Num Participantes', fontsize=12)
ax3.set_title('Prazo x Participantes', fontsize=13)

# 4) Convergencia
ax4 = fig.add_subplot(gs[1, 1])
iters = [r['max_iter'] for r in iteracoes_log]
ratios = [r['ratio'] for r in iteracoes_log]
ax4.plot(iters, ratios, 'ko-', linewidth=2, markersize=8)
ax4.fill_between(iters, ratios, alpha=0.1, color='blue')
ax4.set_xlabel('Iteracoes', fontsize=12)
ax4.set_ylabel('Between SS / Total SS', fontsize=12)
ax4.set_title('Convergencia do K-Means', fontsize=13)
ax4.set_xscale('log')
ax4.axhline(y=ratios[-1], color='red', linestyle='--', alpha=0.5,
            label=f'Final: {ratios[-1]:.3f}')
ax4.legend()

# 5) Cotovelo
ax5 = fig.add_subplot(gs[1, 2])
ks = [r['k'] for r in resultados_k]
ws = [r['within_ss'] for r in resultados_k]
ax5.plot(ks, ws, 'bo-', linewidth=2, markersize=8)
ax5.scatter([5], [resultados_k[3]['within_ss']], c='red', s=200,
            zorder=5, marker='*', label='K=5 (escolhido)')
ax5.set_xlabel('K (num. clusters)', fontsize=12)
ax5.set_ylabel('Within-Cluster SS', fontsize=12)
ax5.set_title('Metodo do Cotovelo', fontsize=13)
ax5.set_xticks(range(2, 12))
ax5.legend(fontsize=10)

# 6) Tamanho dos clusters
ax6 = fig.add_subplot(gs[2, 0])
sizes = df_feat_r['cluster'].value_counts().sort_index()
bars = ax6.bar(range(5), sizes.values, color=colors,
               edgecolor='white', linewidth=2)
ax6.set_xlabel('Cluster', fontsize=12)
ax6.set_ylabel('Qtd Processos', fontsize=12)
ax6.set_title('Tamanho de cada Cluster', fontsize=13)
for bar, val in zip(bars, sizes.values):
    ax6.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 10, str(val),
             ha='center', fontsize=11, fontweight='bold')

# 7) Radar dos centros padronizados
ax7 = fig.add_subplot(gs[2, 1:], polar=True)
angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False).tolist()
angles += angles[:1]
feat_labels = ['Valor\n(log)', 'Prazo\n(dias)', 'Participantes']
for i, c_std in enumerate(centros_std):
    vals3 = [c_std[j] for j in range(len(features))]
    values = vals3 + [vals3[0]]
    ax7.plot(angles, values, 'o-', color=colors[i],
             linewidth=2, label=f'C{i}', markersize=6)
    ax7.fill(angles, values, color=colors[i], alpha=0.08)
ax7.set_xticks(angles[:-1])
ax7.set_xticklabels(feat_labels, fontsize=11)
ax7.set_title('Perfil dos Centros (padronizado)\n', fontsize=13)
ax7.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)

plt.savefig('./dados_sinteticos/analise_clusters_detalhada.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("\nGrafico salvo: ./dados_sinteticos/analise_clusters_detalhada.png")

h2o.cluster().shutdown(prompt=False)
print("\n" + "=" * 80)
print("FIM DA ANALISE")
print("=" * 80)
