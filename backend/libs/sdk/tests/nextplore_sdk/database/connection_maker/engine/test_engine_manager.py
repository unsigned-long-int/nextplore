import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from nextplore_sdk.database.connection_maker.engine.engine_manager import EngineManager


class EngineManagerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.patcher_build = patch('nextplore_sdk.database.connection_maker.engine.engine_manager.build_engine', new_callable=AsyncMock)
        self.mock_build_engine = self.patcher_build.start()

        self.current_time = 1000.0

        def fake_monotonic():
            return self.current_time

        self.patcher_time = patch('nextplore_sdk.database.connection_maker.engine.engine_manager.time.monotonic', side_effect=fake_monotonic)
        self.mock_monotonic = self.patcher_time.start()

        self.addCleanup(self.patcher_build.stop)
        self.addCleanup(self.patcher_time.stop)

    @staticmethod
    def _make_engine(name='engine'):
        eng = MagicMock(name=name)
        eng.dispose = MagicMock(name=f'{name}.dispose')
        return eng

    async def test_reuse_same_profile_without_rebuild(self):
        manager = EngineManager(maxsize=8, idle_ttl=60)
        engine1 = self._make_engine('engine1')
        self.mock_build_engine.return_value = engine1

        profile = MagicMock()

        got1 = await manager.acquire_engine(profile)
        self.current_time += 1.0
        got2 = await manager.acquire_engine(profile)

        self.assertIs(got1, engine1)
        self.assertIs(got2, engine1)
        self.mock_build_engine.assert_awaited_once()
        engine1.dispose.assert_not_called()

    async def test_lru_eviction_disposes_oldest_engines_when_maxsize_exceeded(self):
        manager = EngineManager(maxsize=2, idle_ttl=None)

        e_a = self._make_engine('engineA')
        e_b = self._make_engine('engineB')
        e_c = self._make_engine('engineC')
        e_d = self._make_engine('engineD')
        self.mock_build_engine.side_effect = [e_a, e_b, e_c, e_d]

        a, b, c, d = MagicMock(), MagicMock(), MagicMock(), MagicMock()

        got_a = await manager.acquire_engine(a)
        self.current_time += 0.1
        got_b = await manager.acquire_engine(b)

        self.current_time += 0.1
        got_c = await manager.acquire_engine(c)

        self.current_time += 0.1
        got_d = await manager.acquire_engine(d)

        self.assertIs(got_a, e_a)
        self.assertIs(got_b, e_b)
        self.assertIs(got_c, e_c)
        self.assertIs(got_d, e_d)

        e_a.dispose.assert_called_once()
        e_b.dispose.assert_called_once()
        e_c.dispose.assert_not_called()
        e_d.dispose.assert_not_called()

        self.assertEqual(self.mock_build_engine.await_count, 4)

    async def test_prune_idle_engines_by_ttl(self):
        idle_ttl = 10
        manager = EngineManager(maxsize=8, idle_ttl=idle_ttl)

        e_old = self._make_engine('engineOld')
        e_new = self._make_engine('engineNew')
        self.mock_build_engine.side_effect = [e_old, e_new]

        old_profile = MagicMock()
        new_profile = MagicMock()

        got_old = await manager.acquire_engine(old_profile)
        self.assertIs(got_old, e_old)

        self.current_time += idle_ttl + 1

        got_new = await manager.acquire_engine(new_profile)
        self.assertIs(got_new, e_new)

        e_old.dispose.assert_called_once()
        e_new.dispose.assert_not_called()

    async def test_shutdown_disposes_all(self):
        manager = EngineManager(maxsize=8, idle_ttl=None)

        e1 = self._make_engine('engine1')
        e2 = self._make_engine('engine2')
        self.mock_build_engine.side_effect = [e1, e2]

        p1, p2 = MagicMock(), MagicMock()

        await manager.acquire_engine(p1)
        self.current_time += 0.1
        await manager.acquire_engine(p2)

        await manager.shutdown()

        e1.dispose.assert_called_once()
        e2.dispose.assert_called_once()
        e3 = self._make_engine('engine3')
        self.mock_build_engine.side_effect = [e3]
        got = await manager.acquire_engine(p1)
        self.assertIs(got, e3)
