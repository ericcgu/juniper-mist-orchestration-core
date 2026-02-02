"""
Tests for NMS Configuration API.

These tests validate the ZTP (Zero Touch Provisioning) NMS profile storage.
The profile holds device MACs and network config that gets saved to Redis
and retrieved during site provisioning workflows.

All tests mock Redis to avoid external dependencies.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app


class TestNmsProfile:
    """
    Test the /nms endpoints.
    
    Why: The NMS profile is the foundation for ZTP. Before devices
    can be claimed or configured, we need their MAC addresses and VLAN
    assignments stored in Redis for later retrieval.
    """

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_redis(self):
        """
        Mock Redis client to isolate tests from real Redis.
        
        Why: Tests should never hit real infrastructure. Mocking Redis
        ensures tests are fast, repeatable, and don't require Redis running.
        """
        with patch("src.routers.day0_identity_and_topology.nms.get_redis_client") as mock:
            redis_mock = MagicMock()
            mock.return_value = redis_mock
            yield redis_mock

    @pytest.fixture
    def sample_profile(self):
        """
        Sample deployment profile matching real lab hardware.
        
        Includes:
        - SSR routers (4x) for HA pairs
        - EX switch with management IP
        - AP for wireless coverage
        - VLANs for network segmentation
        """
        return {
            "ssr1_mac": "020001263c58",
            "ssr2_mac": "020001bf1586",
            "ssr3_mac": "020001eb4521",
            "ssr4_mac": "020001263c58",
            "ex1_mac": "d081c527cb80",
            "ap1_mac": "ac2316ed5147",
            "mgmt_vlan": 3623,
            "vlan_1": 3666,
            "vlan_2": 3667,
            "ex_ip": "10.210.6.26",
            "ex_gateway": "10.210.6.30"
        }

    def test_get_profile_found(self, client, mock_redis, sample_profile):
        """
        Test: Retrieve existing profile from Redis.
        
        Why: After POST /nms saves device info, GET /nms must
        return it so other endpoints can use it for ZTP operations.
        """
        # Arrange: Redis has saved profile
        mock_redis.get.return_value = json.dumps(sample_profile)
        
        # Act: Request the profile
        response = client.get("/nms/")
        
        # Assert: Returns saved data
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "found"
        assert data["profile"]["mgmt_vlan"] == 3623
        assert data["profile"]["ssr1_mac"] == "020001263c58"

    def test_get_profile_not_found(self, client, mock_redis):
        """
        Test: Return 404 when no profile exists.
        
        Why: Before Day 0 setup, no profile exists. The API should
        return 404 so automation knows to prompt for device info.
        """
        # Arrange: Redis returns None (no profile saved)
        mock_redis.get.return_value = None
        
        # Act
        response = client.get("/nms/")
        
        # Assert: 404 indicates missing profile
        assert response.status_code == 404

    def test_delete_profile(self, client, mock_redis):
        """
        Test: Clear profile from Redis.
        
        Why: After a deployment is complete or needs reset, clearing
        the profile allows a fresh start for the next site.
        """
        # Arrange
        mock_redis.delete.return_value = 1
        
        # Act
        response = client.delete("/nms/")
        
        # Assert: Confirms deletion
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        mock_redis.delete.assert_called_once()
