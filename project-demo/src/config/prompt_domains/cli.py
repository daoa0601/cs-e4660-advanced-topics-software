"""
CLI interface for prompt template generation.
"""

import argparse

from .registry import (
    get_domain,
    list_domains,
    generate_experiment_prompts,
    save_prompts_to_file,
)


def main():
    """CLI entry point for prompt generation."""
    parser = argparse.ArgumentParser(
        description="Generate domain-specific prompts for LLM cost experiments"
    )
    parser.add_argument(
        "--domain", "-d",
        choices=list_domains(),
        help="Domain to generate prompts from"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=20,
        help="Number of prompts to generate (default: 20)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default=None,
        help="Filter by difficulty level"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (JSON format)"
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates for the domain"
    )
    parser.add_argument(
        "--list-domains",
        action="store_true",
        help="List all available domains"
    )

    args = parser.parse_args()

    if args.list_domains:
        print("Available domains:")
        for name in list_domains():
            domain = get_domain(name)
            print(f"  {name}: {domain.description}")
        exit(0)

    if not args.domain:
        parser.error("--domain is required unless using --list-domains")

    if args.list_templates:
        domain = get_domain(args.domain)
        print(f"\nTemplates for '{args.domain}' domain:")
        print("-" * 50)
        for t in domain.templates:
            print(f"  {t.name} ({t.difficulty})")
            print(f"    Expected output: {t.expected_output_length}")
        exit(0)

    # Generate prompts
    prompts = generate_experiment_prompts(
        domain=args.domain,
        n_prompts=args.count,
        seed=args.seed,
        difficulty_filter=args.difficulty
    )

    if args.output:
        save_prompts_to_file(prompts, args.output)
        print(f"Saved {len(prompts)} prompts to {args.output}")
    else:
        print(f"\nGenerated {len(prompts)} prompts for '{args.domain}' domain:\n")
        for i, p in enumerate(prompts[:5], 1):  # Show first 5
            print(f"--- Prompt {i} ({p['template_name']}, {p['difficulty']}) ---")
            print(p['prompt'][:300] + "..." if len(p['prompt']) > 300 else p['prompt'])
            print()
        if len(prompts) > 5:
            print(f"... and {len(prompts) - 5} more prompts")


if __name__ == "__main__":
    main()
