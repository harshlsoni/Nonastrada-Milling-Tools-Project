import numpy as np
import torch


class EarlyStopping:
    """Early stops the training if validation loss doesn't improve after a given patience."""
    
    def __init__(self, patience=7, min_delta=0, restore_best_weights=True, verbose=True):
        """
        Args:
            patience (int): How long to wait after last time validation loss improved.
                          Default: 7
            min_delta (float): Minimum change in the monitored quantity to qualify as an improvement.
                             Default: 0
            restore_best_weights (bool): Whether to restore model weights from the epoch with the best value.
                                       Default: True
            verbose (bool): If True, prints a message for each validation loss improvement. 
                          Default: True
        """
        self.patience = patience
        self.min_delta = min_delta
        self.restore_best_weights = restore_best_weights
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.inf
        self.best_model_state = None

    def __call__(self, val_loss, model):
        score = -val_loss

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
        elif score < self.best_score + self.min_delta:
            self.counter += 1
            if self.verbose:
                print(f'EarlyStopping counter: {self.counter} out of {self.patience}')
            if self.counter >= self.patience:
                self.early_stop = True
                if self.restore_best_weights and self.best_model_state is not None:
                    model.load_state_dict(self.best_model_state)
                    if self.verbose:
                        print('Restored best model weights')
        else:
            self.best_score = score
            self.save_checkpoint(val_loss, model)
            self.counter = 0

    def save_checkpoint(self, val_loss, model):
        '''Saves model when validation loss decrease.'''
        if self.verbose:
            print(f'Validation loss decreased ({self.val_loss_min:.6f} --> {val_loss:.6f}). Saving model checkpoint...')
        if self.restore_best_weights:
            self.best_model_state = model.state_dict().copy()
        self.val_loss_min = val_loss