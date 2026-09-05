from __future__ import annotations

import argparse

from simulator.simulation.recovery_simulation_report import (
    RecoverySimulationReport,
)

from simulator.simulation.recovery_simulation_service import (
    RecoverySimulationService,
)


def build_parser() -> argparse.ArgumentParser:
    """
    Build the RecoverX simulator CLI parser.
    """

    parser = argparse.ArgumentParser(
        prog="recoverx-simulator",
        description=(
            "Run a RecoverX payment recovery "
            "simulation."
        ),
    )

    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help=(
            "Number of synthetic payments "
            "to simulate."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Optional random seed for "
            "deterministic simulation."
        ),
    )

    return parser


def print_report(
    report: RecoverySimulationReport,
) -> None:
    """
    Print a human-readable simulation report.
    """

    print()

    print("=" * 60)

    print(
        "RECOVERX RECOVERY SIMULATION REPORT"
    )

    print("=" * 60)

    print(
        f"Total payments:          "
        f"{report.total_payments}"
    )

    print(
        f"Payments flagged:        "
        f"{report.payments_flagged}"
    )

    print(
        f"Recovery attempts:       "
        f"{report.recovery_attempts}"
    )

    print(
        f"Successful recoveries:   "
        f"{report.successful_recoveries}"
    )

    print(
        f"Failed recoveries:       "
        f"{report.failed_recoveries}"
    )

    print(
        f"Blocked recoveries:      "
        f"{report.blocked_recoveries}"
    )

    print(
        f"Approval required:       "
        f"{report.approval_required}"
    )

    print(
        f"Escalations:             "
        f"{report.escalations}"
    )

    print(
        f"Recovery rate:           "
        f"{report.recovery_rate:.2f}%"
    )

    print(
        f"Flag rate:               "
        f"{report.payment_flag_rate:.2f}%"
    )

    print(
        f"Escalation rate:         "
        f"{report.escalation_rate:.2f}%"
    )

    print(
        f"Revenue recovered:       "
        f"{report.revenue_recovered:.2f}"
    )

    print(
        f"Average revenue/success: "
        f"{report.average_revenue_per_success:.2f}"
    )

    print("=" * 60)


def main() -> None:
    """
    Run the RecoverX simulation CLI.
    """

    parser = build_parser()

    args = parser.parse_args()

    service = (
        RecoverySimulationService()
    )

    batch_result = service.run(
        count=args.count,
        seed=args.seed,
    )

    report = (
        RecoverySimulationReport.from_batch_result(
            batch_result
        )
    )

    print_report(
        report
    )


if __name__ == "__main__":
    main()