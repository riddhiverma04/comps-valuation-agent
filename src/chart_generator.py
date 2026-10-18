import matplotlib.pyplot as plt
from src.schema import ValuationSummary

def generate_comps_chart(valuations: list[ValuationSummary], filename: str = "comps_chart.png"):
    """Generates a professional bar chart comparing EV / EBITDA multiples across peer companies."""
    print("Generating peer group valuation chart...")
    
    if not valuations:
        print("No valuation data available to plot.")
        return

    tickers = [v.ticker for v in valuations]
    ev_ebitda_multiples = [v.ev_to_ebitda for v in valuations]

    # Set professional styling matching institutional color palettes (Navy blue)
    plt.figure(figsize=(10, 6))
    bars = plt.bar(tickers, ev_ebitda_multiples, color="#1F4E78", edgecolor="#002060", width=0.5)

    # Add titles and labels
    plt.title("Peer Group Valuation Comparison: EV / EBITDA", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Ticker", fontsize=11, fontweight="bold")
    plt.ylabel("EV / EBITDA (x)", fontsize=11, fontweight="bold")
    
    # Grid lines for readability
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Annotate value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.2,
            f"{height:.1f}x",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )

    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()
    print(f"Successfully saved peer comparison chart to {filename}!")