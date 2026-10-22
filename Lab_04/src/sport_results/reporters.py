from sport_results.models import RankingTable


class ConsoleReporter:
    def report(self, table: RankingTable) -> str:
        lines = [table.title, "-" * 44]
        for entry in table:
            lines.append(
                f"{entry.place:>2}. {entry.athlete.name:18}"
                f"{entry.athlete.category:11}{entry.value:7.2f}"
            )
        return "\n".join(lines)


class MarkdownReporter:
    def report(self, table: RankingTable) -> str:
        lines = [
            f"### {table.title}",
            "| # | Спортсмен | Бали |",
            "|---|---|---|",
        ]
        for entry in table:
            lines.append(
                f"| {entry.place} | {entry.athlete.name} | {entry.value:.2f} |"
            )
        return "\n".join(lines)


class DictExporter:
    def export(self, table: RankingTable) -> list[dict[str, str]]:
        return [
            {
                "place": str(entry.place),
                "athlete": entry.athlete.name,
                "value": f"{entry.value:.2f}",
            }
            for entry in table
        ]
