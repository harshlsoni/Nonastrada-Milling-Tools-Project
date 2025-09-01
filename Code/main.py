import torch
from torch.utils.data import DataLoader, random_split
import pandas as pd
from MultiModalMillingDataset import MultiModalMillingDataset
from MultiTrainer import MultiTrainer


if __name__ == "__main__":
    # Load dataset
    data = MultiModalMillingDataset("Files", "Files\\labels.csv", "Files\\labels_reg.csv")
    
    # Train/Validation split
    train_size = int(0.8 * len(data))   # 80% training
    val_size = len(data) - train_size
    train_dataset, val_dataset = random_split(data, [train_size, val_size])

    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Initialize MultiTrainer
    trainer = MultiTrainer(
        train_loader=train_loader,
        val_loader=val_loader,
        num_classes=3,
        device=device,
        epochs=20
    )
    
    # Show model architecture summary
    trainer.get_model_summary()
    
    # Choose training mode: 'parallel' or 'sequential'
    training_mode = 'sequential'  # Change to 'parallel' for parallel training
    
    if training_mode == 'parallel':
        # Train all models in parallel (faster but uses more GPU memory)
        print("\n🚀 Starting PARALLEL training...")
        results = trainer.train_all_parallel()
    else:
        # Train all models sequentially (slower but more memory efficient)
        print("\n🚀 Starting SEQUENTIAL training...")
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
    print(f"\n✅ Basic comparison results saved to 'model_comparison_results.csv'")
    
    print("\n" + "="*80)
    print("🎉 TRAINING COMPLETE!")
    print("="*80)
    print("📊 Results saved in:")
    print("   - training_results/ (detailed CSV files)")
    print("   - saved_models/ (trained models + loading script)")
    print("   - model_comparison.png (training curves)")
    print("   - model_comparison_results.csv (basic comparison)")
    print("="*80)