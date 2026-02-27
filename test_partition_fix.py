#!/usr/bin/env python3
"""
Test and fix the partition_context method.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_current_partition():
    """Test the current partition logic."""
    from swarm_v2.core.trm_orchestrator import TRMOrchestrator
    
    # Create orchestrator without base agent
    orchestrator = TRMOrchestrator(None)
    
    test_cases = [
        ("Single line no spaces", "ThisIsASingleLineWithNoSpaces", 4),
        ("Single line with spaces", "This is a single line with spaces", 4),
        ("Multiple lines", "Line1\nLine2\nLine3\nLine4\nLine5", 4),
        ("Long single line", "word " * 100, 4),
        ("Symbolic numbers", "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16", 4),
        ("Mixed content", "First line\nSecond line with more text\nThird\nFourth", 4),
    ]
    
    print("Testing current partition_context method:")
    print("="*60)
    
    for name, context, num_parts in test_cases:
        partitions = orchestrator.partition_context(context, num_parts)
        print(f"\n{name}:")
        print(f"  Context length: {len(context)} chars")
        print(f"  Lines in context: {len(context.split(chr(10)))}")
        print(f"  Requested partitions: {num_parts}")
        print(f"  Actual partitions: {len(partitions)}")
        if partitions:
            for i, part in enumerate(partitions[:3]):  # Show first 3
                print(f"    Part {i+1}: {len(part)} chars: {part[:50]}...")
    
    return orchestrator

def propose_fix():
    """Propose a better partition method."""
    print("\n" + "="*60)
    print("Proposed fix for partition_context:")
    print("="*60)
    
    def better_partition_context(context: str, num_partitions: int) -> List[str]:
        """
        Better partition context for parallel processing.
        
        For text context, uses semantic boundaries (sentences, paragraphs).
        For symbolic context, uses equal partitioning.
        For single-line content, splits by spaces or equal chunks.
        """
        if not context:
            return []
            
        # Count newlines
        lines = context.split('\n')
        
        if len(lines) > 1:
            # Multiple lines: partition by lines
            if len(lines) > num_partitions:
                # More lines than partitions: group lines
                partition_size = len(lines) // num_partitions
                partitions = []
                for i in range(num_partitions):
                    start = i * partition_size
                    end = (i + 1) * partition_size if i < num_partitions - 1 else len(lines)
                    partition = '\n'.join(lines[start:end])
                    if partition:
                        partitions.append(partition)
                return partitions
            else:
                # Fewer lines than partitions: each line gets its own partition
                return [line for line in lines if line.strip()]
        else:
            # Single line: need smarter partitioning
            line = lines[0]
            
            # Check if it's symbolic (mostly numbers and spaces)
            numeric_chars = sum(1 for c in line if c.isdigit() or c.isspace())
            is_symbolic = numeric_chars / len(line) > 0.7
            
            if is_symbolic:
                # Symbolic: split by spaces
                tokens = line.split()
                if len(tokens) > num_partitions:
                    # Group tokens
                    token_partition_size = len(tokens) // num_partitions
                    partitions = []
                    for i in range(num_partitions):
                        start = i * token_partition_size
                        end = (i + 1) * token_partition_size if i < num_partitions - 1 else len(tokens)
                        partition = ' '.join(tokens[start:end])
                        if partition:
                            partitions.append(partition)
                    return partitions
                else:
                    # Fewer tokens than partitions: each token gets its own partition
                    return [token for token in tokens if token]
            else:
                # Text: split by sentences or equal chunks
                # Simple approach: split by spaces
                words = line.split()
                if len(words) > num_partitions * 5:  # At least 5 words per partition
                    # Group words
                    words_per_partition = len(words) // num_partitions
                    partitions = []
                    for i in range(num_partitions):
                        start = i * words_per_partition
                        end = (i + 1) * words_per_partition if i < num_partitions - 1 else len(words)
                        partition = ' '.join(words[start:end])
                        if partition:
                            partitions.append(partition)
                    return partitions
                else:
                    # Not enough words for meaningful partitioning
                    # Return equal character chunks
                    chunk_size = len(line) // num_partitions
                    if chunk_size < 10:  # Too small chunks
                        return [line]  # Don't partition
                    
                    partitions = []
                    for i in range(num_partitions):
                        start = i * chunk_size
                        end = (i + 1) * chunk_size if i < num_partitions - 1 else len(line)
                        partition = line[start:end]
                        if partition:
                            partitions.append(partition)
                    return partitions
    
    # Import List for type hint
    from typing import List
    
    # Test the proposed fix
    test_cases = [
        ("Single line no spaces", "ThisIsASingleLineWithNoSpaces", 4),
        ("Single line with spaces", "This is a single line with spaces", 4),
        ("Long single line", "word " * 100, 4),
        ("Symbolic numbers", "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16", 4),
    ]
    
    for name, context, num_parts in test_cases:
        partitions = better_partition_context(context, num_parts)
        print(f"\n{name}:")
        print(f"  Context length: {len(context)} chars")
        print(f"  Requested partitions: {num_parts}")
        print(f"  Actual partitions: {len(partitions)}")
        if partitions:
            for i, part in enumerate(partitions[:3]):  # Show first 3
                print(f"    Part {i+1}: {len(part)} chars: {part[:50]}...")
    
    print("\n" + "="*60)
    print("Implementation notes:")
    print("1. Handle single-line content better")
    print("2. Distinguish between symbolic and text content")
    print("3. Ensure minimum partition size (e.g., 10 chars)")
    print("4. Fall back to no partition if chunks would be too small")

def main():
    print("PARTITION CONTEXT FIX ANALYSIS")
    print("="*60)
    
    test_current_partition()
    propose_fix()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("The current partition_context method fails for single-line content")
    print("because it only partitions by newlines. Need to add handling for")
    print("single-line content by splitting on spaces or creating equal chunks.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())