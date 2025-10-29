"""Reinforcement learning environment for dynamic fraud decision optimization."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces

LOGGER = logging.getLogger("aegis.models.rl")


@dataclass
class FraudDecisionEnvConfig:
    reward_block_fraud: float = 100.0
    reward_allow_legit: float = 1.0
    penalty_block_legit: float = -50.0
    penalty_allow_fraud: float = -200.0
    penalty_flag: float = -10.0
    reward_flag_fraud: float = 50.0


class FraudDecisionEnv(gym.Env):
    """Custom RL environment for fraud decision making."""

    metadata = {"render.modes": ["human"]}

    def __init__(self, historical_transactions: pd.DataFrame, feature_cols: list[str], config: Optional[FraudDecisionEnvConfig] = None) -> None:
        super().__init__()
        self.transactions = historical_transactions.reset_index(drop=True)
        self.feature_cols = feature_cols
        self.config = config or FraudDecisionEnvConfig()

        obs_dim = len(feature_cols)
        self.action_space = spaces.Discrete(3)  # 0=allow, 1=flag, 2=block
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)

        self.current_index = 0

    def reset(self, *, seed: Optional[int] = None, options: Optional[Dict] = None):  # type: ignore[override]
        super().reset(seed=seed)
        self.current_index = 0
        observation = self._get_observation(self.current_index)
        return observation, {}

    def step(self, action: int):  # type: ignore[override]
        if self.current_index >= len(self.transactions):
            return self.observation_space.low, 0.0, True, False, {}

        transaction = self.transactions.iloc[self.current_index]
        is_fraud = bool(transaction.get("is_fraud", 0))

        reward = self._calculate_reward(action, is_fraud)

        self.current_index += 1
        terminated = self.current_index >= len(self.transactions)
        truncated = False
        observation = self._get_observation(self.current_index) if not terminated else self.observation_space.low

        return observation, reward, terminated, truncated, {}

    def _get_observation(self, index: int) -> np.ndarray:
        if index >= len(self.transactions):
            return self.observation_space.low
        features = self.transactions.loc[index, self.feature_cols].to_numpy(dtype=np.float32)
        return features

    def _calculate_reward(self, action: int, is_fraud: bool) -> float:
        cfg = self.config
        if action == 2:  # block
            return cfg.reward_block_fraud if is_fraud else cfg.penalty_block_legit
        if action == 1:  # flag
            return cfg.reward_flag_fraud if is_fraud else cfg.penalty_flag
        return cfg.reward_allow_legit if not is_fraud else cfg.penalty_allow_fraud


