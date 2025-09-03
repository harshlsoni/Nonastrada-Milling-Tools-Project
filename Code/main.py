import os
import torch
import warnings
from torch.utils.data import DataLoader, random_split
import pandas as pd
from MultiModalMillingDataset import MultiModalMillingDataset
from MultiTrainer import MultiTrainer

# Ignore warnings
warnings.filterwarnings('ignore')


if __name__ == "__main__":
    # Load dataset
    data = MultiModalMillingDataset("Files", 
                                   os.path.join("Files", "labels.csv"), 
                                   os.path.join("Files", "labels_reg.csv"))
    
    # Train/Validation split
    train_size = int(0.8 * len(data))   # 80% training
    val_size = len(data) - train_size
    train_dataset, val_dataset = random_split(data, [train_size, val_size])

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Initialize MultiTrainer with early stopping
    trainer = MultiTrainer(
        train_loader=train_loader,
        val_loader=val_loader,
        num_classes=3,
        device=device,
        epochs=50,  # Increased epochs since we have early stopping
        early_stopping_patience=10  # Stop if no improvement for 10 epochs
    )
    
    # Show model architecture summary
    trainer.get_model_summary()
    
    # Choose training mode: 'parallel' or 'sequential'
    training_mode = 'sequential'  # Change to 'parallel' for parallel training
    
    if training_mode == 'parallel':
        # Train all models in parallel (faster but uses more GPU memory)
        print("\nStarting PARALLEL training...")
        results = trainer.train_all_parallel()
    else:
        # Train all models sequentially (slower but more memory efficient)
        print("\nStarting SEQUENTIAL training...")
        results = trainer.train_all_sequential()
    
    # Compare results
    comparison = trainer.compare_results()
    
    # Plot training curves
    trainer.plot_training_curves()
    
    # Save detailed results to CSV files
    print("\n" + "="*60)
    print("SAVING DETAILED RESULTS")
    print("="*60)
    detailed_df, summary_df = trainer.save_detailed_results_to_csv()
    
    # Save trained models
    print("\n" + "="*60)
    print("SAVING TRAINED MODELS")
    print("="*60)
    trainer.save_trained_models()
    
    # Save basic comparison results (keeping original functionality)
    df_comparison = pd.DataFrame(comparison)
    df_comparison.to_csv('model_comparison_results.csv', index=False)
    print(f"\nBasic comparison results saved to 'model_comparison_results.csv'")
    
    # Hyperparameter tuning on the best model
    print("\n" + "="*80)
    print("STARTING HYPERPARAMETER TUNING ON BEST MODEL")
    print("="*80)
    
    try:
        best_config, best_score, tuning_results, tuning_df = trainer.tune_best_model_hyperparameters(
            max_trials=15,  # Reduced for faster execution
            max_epochs=30,  # Reduced for faster execution
            patience=8      # Early stopping patience for tuning
        )
        
        print(f"\nHyperparameter tuning completed successfully!")
        print(f"Best tuned accuracy: {best_score:.4f}")
        
    except Exception as e:
        print(f"Error during hyperparameter tuning: {e}")
        print("Continuing without hyperparameter tuning...")
    
    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
    print("Results saved in:")
    print("   - training_results/ (detailed CSV files)")
    print("   - saved_models/ (trained models + loading script)")
    print("   - model_comparison.png (training curves)")
    print("   - model_comparison_results.csv (basic comparison)")
    print("   - *_hyperparameter_tuning_results.csv (hyperparameter tuning results)")
    print("="*80)
    
    # Print final model comparison
    print("\n" + "="*60)
    print("FINAL MODEL PERFORMANCE SUMMARY")
    print("="*60)
    
    # Sort models by best validation accuracy
    sorted_results = sorted(trainer.results.items(), 
                          key=lambda x: x[1]['best_val_acc'], 
                          reverse=True)
    
    for i, (model_name, results) in enumerate(sorted_results, 1):
        status = "WINNER" if i == 1 else f"{i}."
        early_stop_info = " (Early Stopped)" if results.get('early_stopped', False) else ""
        print(f"{status} {model_name}: {results['best_val_acc']:.4f} accuracy "
              f"({results['epochs_trained']}/{trainer.epochs} epochs{early_stop_info})")
    
    print("="*60)