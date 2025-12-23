"""
Main pipeline orchestrator.
Coordinates ingestion, normalization, validation, aggregation, and reporting.
"""
import os
import sys
import logging
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from ingestion import ingest_all_files
from normalizer import normalize_all_files
from validator import validate_all_data
from aggregator import compute_aggregated_metrics, get_all_clients
from report_generator import generate_all_reports

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_pipeline(data_dir: str, output_dir: str, fail_on_validation: bool = False):
    """
    Run the complete portfolio analytics pipeline.
    
    Args:
        data_dir: Directory containing broker export files
        output_dir: Directory for output reports
        fail_on_validation: If True, stop pipeline on validation errors
    
    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("PORTFOLIO ANALYTICS PIPELINE")
    logger.info(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    try:
        # Validate input directories
        data_path = Path(data_dir)
        if not data_path.exists():
            error_msg = f"Data directory does not exist: {data_dir}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            return False
        
        # Step 1: Ingestion
        logger.info("\n[1/5] Ingesting broker files...")
        print("\n[1/5] Ingesting broker files...")
        
        try:
            ingested_files = ingest_all_files(data_dir)
            
            if not ingested_files:
                error_msg = "No files were successfully ingested"
                logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                return False
            
            logger.info(f"Successfully ingested {len(ingested_files)} files")
            print(f"✓ Ingested {len(ingested_files)} files")
            
        except Exception as e:
            error_msg = f"Error during ingestion: {str(e)}"
            logger.exception(error_msg)
            print(f"ERROR: {error_msg}")
            return False
        
        # Step 2: Normalization
        logger.info("\n[2/5] Normalizing data to canonical schemas...")
        print("\n[2/5] Normalizing data to canonical schemas...")
        
        try:
            normalized_data = normalize_all_files(ingested_files)
            
            trades_df = normalized_data['trades']
            cg_df = normalized_data['capital_gains']
            
            logger.info(f"Normalized {len(trades_df)} trade records")
            logger.info(f"Normalized {len(cg_df)} capital gains records")
            print(f"✓ Normalized {len(trades_df)} trade records")
            print(f"✓ Normalized {len(cg_df)} capital gains records")
            
        except Exception as e:
            error_msg = f"Error during normalization: {str(e)}"
            logger.exception(error_msg)
            print(f"ERROR: {error_msg}")
            return False
        
        # Step 3: Validation
        logger.info("\n[3/5] Validating data quality...")
        print("\n[3/5] Validating data quality...")
        
        try:
            validation_results = validate_all_data(trades_df, cg_df)
            
            if validation_results['is_valid']:
                logger.info("All data passed validation")
                print("✓ All data passed validation")
            else:
                logger.warning(f"Found {validation_results['total_errors']} validation errors")
                print(f"⚠ Found {validation_results['total_errors']} validation errors")
                print(f"  - Trades errors: {len(validation_results['trades_errors'])}")
                print(f"  - Capital gains errors: {len(validation_results['capital_gains_errors'])}")
                
                if fail_on_validation:
                    error_msg = "Stopping pipeline due to validation errors"
                    logger.error(error_msg)
                    print(f"ERROR: {error_msg}")
                    return False
                else:
                    logger.info("Continuing with report generation (errors will be included in reports)")
                    print("  Continuing with report generation (errors will be included in reports)")
            
        except Exception as e:
            error_msg = f"Error during validation: {str(e)}"
            logger.exception(error_msg)
            print(f"ERROR: {error_msg}")
            return False
        
        # Step 4: Aggregation
        logger.info("\n[4/5] Computing aggregated metrics...")
        print("\n[4/5] Computing aggregated metrics...")
        
        try:
            clients = get_all_clients(trades_df, cg_df)
            logger.info(f"Found {len(clients)} clients: {', '.join(clients)}")
            print(f"✓ Found {len(clients)} clients: {', '.join(clients)}")
            
        except Exception as e:
            error_msg = f"Error during aggregation: {str(e)}"
            logger.exception(error_msg)
            print(f"ERROR: {error_msg}")
            return False
        
        # Step 5: Report Generation
        logger.info("\n[5/5] Generating reports...")
        print("\n[5/5] Generating reports...")
        
        try:
            # Ensure output directory exists
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            generate_all_reports(trades_df, cg_df, validation_results, output_dir)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETE")
            logger.info(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Reports generated in: {output_dir}")
            logger.info("=" * 80)
            
            print("\n" + "=" * 80)
            print("PIPELINE COMPLETE")
            print("=" * 80)
            print(f"Reports generated in: {output_dir}")
            print(f"Duration: {duration:.2f} seconds")
            
            return True
            
        except Exception as e:
            error_msg = f"Error during report generation: {str(e)}"
            logger.exception(error_msg)
            print(f"ERROR: {error_msg}")
            return False
    
    except Exception as e:
        error_msg = f"Unexpected error in pipeline: {str(e)}"
        logger.exception(error_msg)
        print(f"ERROR: {error_msg}")
        return False


def main():
    """Main entry point."""
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Default paths
    data_dir = project_root / "data"
    output_dir = project_root / "reports"
    
    # Check if data directory exists
    if not data_dir.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)
    
    # Run pipeline
    success = run_pipeline(str(data_dir), str(output_dir), fail_on_validation=False)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
