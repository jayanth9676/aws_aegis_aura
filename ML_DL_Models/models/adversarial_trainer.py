"""Adversarial example generation utilities for fraud detection models."""

from __future__ import annotations

import logging
from typing import Callable

import numpy as np
import torch
import torch.nn as nn

LOGGER = logging.getLogger("aegis.models.adversarial")


def fgsm_attack(model: nn.Module, loss_fn: Callable, data: torch.Tensor, label: torch.Tensor, epsilon: float = 0.01) -> torch.Tensor:
    """Fast Gradient Sign Method attack."""

    data_adv = data.clone().detach().requires_grad_(True)
    output = model(data_adv)
    loss = loss_fn(output, label)
    loss.backward()
    perturbed_data = data_adv + epsilon * data_adv.grad.sign()
    return torch.clamp(perturbed_data, 0.0, 1.0).detach()


def pgd_attack(
    model: nn.Module,
    loss_fn: Callable,
    data: torch.Tensor,
    label: torch.Tensor,
    epsilon: float = 0.03,
    alpha: float = 0.005,
    num_iterations: int = 40,
) -> torch.Tensor:
    """Projected Gradient Descent attack for stronger adversarial examples."""

    data_adv = data.clone().detach()
    data_orig = data.clone().detach()

    for _ in range(num_iterations):
        data_adv.requires_grad_(True)
        output = model(data_adv)
        loss = loss_fn(output, label)
        loss.backward()

        with torch.no_grad():
            data_adv = data_adv + alpha * data_adv.grad.sign()
            eta = torch.clamp(data_adv - data_orig, min=-epsilon, max=epsilon)
            data_adv = torch.clamp(data_orig + eta, 0.0, 1.0)
        data_adv = data_adv.detach()

    return data_adv


