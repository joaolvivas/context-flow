"""
User Profile Manager - Persistent user context

Maintains user profiles that are always injected into conversations.
Stores identity, goals, preferences, and key facts about each user.

This ensures the AI always "remembers" who you are, even in new chats.
"""
import json
import os
from typing import Dict, Optional
from datetime import datetime


class UserProfile:
    """
    Represents a user's persistent profile.

    Contains identity, goals, preferences, and other key context
    that should always be available to the AI.
    """

    def __init__(
        self,
        user_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        goals: Optional[list] = None,
        studying: Optional[list] = None,
        preferences: Optional[Dict] = None,
        custom_context: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Initialize user profile.

        Args:
            user_id: Unique user identifier
            name: User's name
            role: Current role/occupation
            goals: List of user goals
            studying: What user is currently learning
            preferences: User preferences (communication style, etc)
            custom_context: Free-form context text
            metadata: Additional metadata
        """
        self.user_id = user_id
        self.name = name
        self.role = role
        self.goals = goals or []
        self.studying = studying or []
        self.preferences = preferences or {}
        self.custom_context = custom_context
        self.metadata = metadata or {}
        self.created_at = metadata.get("created_at") or datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_context(self) -> str:
        """
        Convert profile to context string for LLM injection.

        Returns:
            Formatted context string
        """
        context_parts = []

        if self.name:
            context_parts.append(f"User: {self.name}")

        if self.role:
            context_parts.append(f"Role: {self.role}")

        if self.goals:
            goals_str = ", ".join(self.goals)
            context_parts.append(f"Goals: {goals_str}")

        if self.studying:
            studying_str = ", ".join(self.studying)
            context_parts.append(f"Currently studying: {studying_str}")

        if self.preferences:
            prefs = []
            for key, value in self.preferences.items():
                prefs.append(f"{key}: {value}")
            context_parts.append(f"Preferences: {', '.join(prefs)}")

        if self.custom_context:
            context_parts.append(self.custom_context)

        if not context_parts:
            return ""

        return "\n".join(context_parts)

    def to_dict(self) -> Dict:
        """Convert profile to dictionary."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "goals": self.goals,
            "studying": self.studying,
            "preferences": self.preferences,
            "custom_context": self.custom_context,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "UserProfile":
        """Create profile from dictionary."""
        return cls(
            user_id=data["user_id"],
            name=data.get("name"),
            role=data.get("role"),
            goals=data.get("goals"),
            studying=data.get("studying"),
            preferences=data.get("preferences"),
            custom_context=data.get("custom_context"),
            metadata=data.get("metadata", {})
        )


class ProfileManager:
    """
    Manages user profiles with persistent storage.

    Profiles are stored as JSON files in a profiles directory.
    Provides CRUD operations and profile caching.
    """

    def __init__(self, profiles_dir: str = "profiles"):
        """
        Initialize profile manager.

        Args:
            profiles_dir: Directory to store profile JSON files
        """
        self.profiles_dir = profiles_dir
        self._cache: Dict[str, UserProfile] = {}

        # Create profiles directory if it doesn't exist
        os.makedirs(self.profiles_dir, exist_ok=True)

    def _get_profile_path(self, user_id: str) -> str:
        """Get file path for a user's profile."""
        # Sanitize user_id for filename
        safe_id = "".join(c for c in user_id if c.isalnum() or c in "._-")
        return os.path.join(self.profiles_dir, f"{safe_id}.json")

    def get(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by ID.

        Args:
            user_id: User identifier

        Returns:
            UserProfile if exists, None otherwise
        """
        # Check cache first
        if user_id in self._cache:
            return self._cache[user_id]

        # Try to load from file
        profile_path = self._get_profile_path(user_id)

        if not os.path.exists(profile_path):
            return None

        try:
            with open(profile_path, "r") as f:
                data = json.load(f)

            profile = UserProfile.from_dict(data)
            self._cache[user_id] = profile
            return profile

        except Exception:
            return None

    def create(self, profile: UserProfile) -> bool:
        """
        Create or update user profile.

        Args:
            profile: UserProfile to save

        Returns:
            True if successful, False otherwise
        """
        try:
            profile.updated_at = datetime.now().isoformat()

            profile_path = self._get_profile_path(profile.user_id)

            with open(profile_path, "w") as f:
                json.dump(profile.to_dict(), f, indent=2)

            # Update cache
            self._cache[profile.user_id] = profile

            return True

        except Exception:
            return False

    def update(self, user_id: str, **updates) -> bool:
        """
        Update specific fields of a user profile.

        Args:
            user_id: User identifier
            **updates: Fields to update

        Returns:
            True if successful, False otherwise
        """
        profile = self.get(user_id)

        if not profile:
            # Create new profile
            profile = UserProfile(user_id=user_id)

        # Update fields
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        return self.create(profile)

    def delete(self, user_id: str) -> bool:
        """
        Delete user profile.

        Args:
            user_id: User identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            profile_path = self._get_profile_path(user_id)

            if os.path.exists(profile_path):
                os.remove(profile_path)

            # Remove from cache
            if user_id in self._cache:
                del self._cache[user_id]

            return True

        except Exception:
            return False

    def list_profiles(self) -> list[str]:
        """
        List all user IDs with profiles.

        Returns:
            List of user IDs
        """
        profiles = []

        for filename in os.listdir(self.profiles_dir):
            if filename.endswith(".json"):
                user_id = filename[:-5]  # Remove .json
                profiles.append(user_id)

        return profiles

    def get_or_create(self, user_id: str, **defaults) -> UserProfile:
        """
        Get existing profile or create new one with defaults.

        Args:
            user_id: User identifier
            **defaults: Default values for new profile

        Returns:
            UserProfile (existing or newly created)
        """
        profile = self.get(user_id)

        if profile:
            return profile

        # Create new profile with defaults
        profile = UserProfile(user_id=user_id, **defaults)
        self.create(profile)

        return profile


# Global profile manager instance
_profile_manager: Optional[ProfileManager] = None


def get_profile_manager(profiles_dir: str = "profiles") -> ProfileManager:
    """
    Get or create global profile manager instance.

    Args:
        profiles_dir: Directory for profile storage

    Returns:
        ProfileManager instance
    """
    global _profile_manager

    if _profile_manager is None:
        _profile_manager = ProfileManager(profiles_dir=profiles_dir)

    return _profile_manager
