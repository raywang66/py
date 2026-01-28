"""
Skin Color Matcher - Usage Example
Demonstrates how to use the production-grade skin color matching tool

Author: CV/Image Processing Engineer
"""

from skin_color_matcher import SkinColorMatcher
from pathlib import Path


def example_basic_usage():
    """Basic usage example"""
    print("=" * 80)
    print("EXAMPLE 1: Basic Skin Color Matching")
    print("=" * 80)

    # Initialize matcher with GPU acceleration
    matcher = SkinColorMatcher(use_gpu=True)

    # Analyze two images
    # adjustments = matcher.analyze(
    #     reference_path="reference_portrait.jpg",  # Your reference JPEG/PNG
    #     test_raw_path="test_portrait.ARW",        # Your Sony RAW file
    #     output_dir="output"                       # Results will be saved here
    # )
    adjustments = matcher.analyze(
        reference_path="./Photos/IMG_2571.JPG",  # Your reference JPEG/PNG
        test_raw_path="./Photos/DSC05171.ARW",        # Your Sony RAW file
        output_dir="output"                       # Results will be saved here
    )

    print(f"\n✅ Analysis complete!")
    print(f"HSL Orange Hue adjustment: {adjustments.hsl_hue_orange:+d}")
    print(f"HSL Orange Saturation adjustment: {adjustments.hsl_sat_orange:+d}")


def example_batch_processing():
    """Batch process multiple RAW files against one reference"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Batch Processing Multiple RAW Files")
    print("=" * 80)

    matcher = SkinColorMatcher(use_gpu=True)

    reference = "reference_portrait.jpg"
    raw_files = [
        "portrait_001.ARW",
        "portrait_002.ARW",
        "portrait_003.ARW"
    ]

    results = {}
    for raw_file in raw_files:
        print(f"\nProcessing: {raw_file}")
        try:
            adj = matcher.analyze(
                reference_path=reference,
                test_raw_path=raw_file,
                output_dir=f"output/{Path(raw_file).stem}"
            )
            results[raw_file] = adj
        except Exception as e:
            print(f"❌ Failed to process {raw_file}: {e}")

    print(f"\n✅ Batch processing complete! Processed {len(results)} files.")


def example_custom_workflow():
    """Advanced usage with custom workflow"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Custom Workflow with Intermediate Steps")
    print("=" * 80)

    matcher = SkinColorMatcher(use_gpu=True)

    # Step 1: Load images separately
    ref_img = matcher.load_reference_image("reference.jpg")
    test_img = matcher.load_raw_image("test.ARW", apply_gamma=True)

    print(f"Reference shape: {ref_img.shape}")
    print(f"Test shape: {test_img.shape}")

    # Step 2: Extract skin masks
    ref_mask = matcher.extract_skin_mask(ref_img)
    test_mask = matcher.extract_skin_mask(test_img)

    print(f"Reference skin pixels: {ref_mask.sum()}")
    print(f"Test skin pixels: {test_mask.sum()}")

    # Step 3: Compute statistics
    ref_stats = matcher.compute_color_statistics(ref_img, ref_mask)
    test_stats = matcher.compute_color_statistics(test_img, test_mask)

    print(f"\nReference HSL: H={ref_stats.h_mean:.1f}°, S={ref_stats.s_mean:.3f}, L={ref_stats.l_mean:.3f}")
    print(f"Test HSL:      H={test_stats.h_mean:.1f}°, S={test_stats.s_mean:.3f}, L={test_stats.l_mean:.3f}")

    # Step 4: Compute adjustments
    adj = matcher.compute_lightroom_adjustments(ref_stats, test_stats)

    # Step 5: Visualize
    matcher.visualize_results(
        ref_img, test_img, ref_mask, test_mask,
        ref_stats, test_stats, adj,
        save_path="custom_analysis.png"
    )

    print("✅ Custom workflow complete!")


def example_cpu_only():
    """Example for CPU-only processing (no CUDA)"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: CPU-Only Mode (No GPU Required)")
    print("=" * 80)

    # Disable GPU
    matcher = SkinColorMatcher(use_gpu=False)

    adjustments = matcher.analyze(
        reference_path="reference.jpg",
        test_raw_path="test.ARW",
        output_dir="output_cpu"
    )

    print("✅ CPU-only analysis complete!")


def example_error_handling():
    """Example with proper error handling"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Production Error Handling")
    print("=" * 80)

    matcher = SkinColorMatcher(use_gpu=True)

    try:
        adjustments = matcher.analyze(
            reference_path="reference.jpg",
            test_raw_path="test.ARW",
            output_dir="output"
        )

        # Save adjustments to file for later use
        import json
        from dataclasses import asdict

        with open("lightroom_adjustments.json", "w") as f:
            json.dump(asdict(adjustments), f, indent=2)

        print("✅ Adjustments saved to lightroom_adjustments.json")

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except ValueError as e:
        print(f"❌ Invalid data: {e}")
    except RuntimeError as e:
        print(f"❌ CUDA error (try CPU mode): {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    # Run examples (comment out the ones you don't need)

    # Basic usage - most common workflow
    example_basic_usage()

    # Batch processing
    # example_batch_processing()

    # Custom workflow
    # example_custom_workflow()

    # CPU-only mode
    # example_cpu_only()

    # Error handling
    # example_error_handling()

    # print("\n" + "=" * 80)
    # print("📝 NOTE: Update the file paths in the examples before running!")
    # print("=" * 80)

