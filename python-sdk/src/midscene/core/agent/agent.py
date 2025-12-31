"""Main Agent class for Midscene automation."""

import time
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

from midscene.shared.logger import get_logger
from midscene.shared.utils import assert_condition
from midscene.core.types import (
    AgentOpt,
    AgentWaitForOpt,
    AgentAssertOpt,
    DetailedLocateParam,
    ExecutionDump,
    GroupedActionDump,
    LocateOption,
    LocateResult,
    LocateResultElement,
    PlanningAction,
    ServiceExtractOption,
    UIContext,
)
from midscene.core.service import Service
from midscene.core.device import AbstractInterface

logger = get_logger("agent")

T = TypeVar("T", bound=AbstractInterface)

# User prompt type
TUserPrompt = Union[str, Dict[str, Any]]


def build_detailed_locate_param(
    prompt: TUserPrompt,
    opt: Optional[LocateOption] = None
) -> DetailedLocateParam:
    """Build detailed locate param from prompt and options."""
    if isinstance(prompt, str):
        return DetailedLocateParam(
            prompt=prompt,
            deep_think=opt.deep_think if opt else False,
        )
    return DetailedLocateParam(
        prompt=prompt.get("prompt", str(prompt)),
        deep_think=opt.deep_think if opt else False,
    )


class Agent(Generic[T]):
    """
    AI-powered automation agent.
    
    The Agent class provides methods to interact with UI elements using
    natural language descriptions. It supports actions like tap, input,
    scroll, and data extraction.
    """
    
    def __init__(
        self,
        interface: T,
        opts: Optional[AgentOpt] = None,
    ):
        """
        Initialize the Agent.
        
        Args:
            interface: The interface to control (e.g., PlaywrightPage)
            opts: Agent options
        """
        self.interface = interface
        self._opts = opts or AgentOpt()
        
        # Initialize service
        self.service = Service(self.get_ui_context)
        
        # Initialize dump storage
        self._dump = self._reset_dump()
        self._destroyed = False
        
        # Frozen context for batch operations
        self._frozen_ui_context: Optional[UIContext] = None
        
        # Dump update listeners
        self._dump_update_listeners: List[Callable] = []
        
        logger.debug("Agent initialized with interface type: %s", 
                    getattr(interface, "interface_type", "unknown"))
    
    @property
    def page(self) -> T:
        """Deprecated: use .interface instead."""
        return self.interface
    
    async def get_ui_context(self, action: Optional[str] = None) -> UIContext:
        """
        Get the current UI context.
        
        Args:
            action: The action being performed
            
        Returns:
            UIContext with screenshot and size
        """
        # If context is frozen, return frozen context
        if self._frozen_ui_context:
            logger.debug("Using frozen page context for action: %s", action)
            return self._frozen_ui_context
        
        # Get context from interface
        if hasattr(self.interface, "get_context"):
            return await self.interface.get_context()
        
        # Fallback: build context from interface methods
        screenshot = await self.interface.screenshot_base64()
        size = await self.interface.size()
        
        from midscene.core.types import SimpleUIContext
        return SimpleUIContext(screenshot_base64=screenshot, size=size)
    
    def _reset_dump(self) -> GroupedActionDump:
        """Reset the action dump."""
        from midscene import __version__
        
        return GroupedActionDump(
            sdk_version=__version__,
            group_name=self._opts.group_name,
            group_description=self._opts.group_description,
            executions=[],
            model_briefs=[],
        )
    
    def _get_model_config(self, intent: str = "default") -> Dict[str, Any]:
        """Get model configuration for the given intent."""
        import os
        
        config = self._opts.model_config_dict or {}
        
        # Merge with environment variables
        model_name = (
            config.get("MIDSCENE_MODEL_NAME") or 
            os.environ.get("MIDSCENE_MODEL_NAME", "gpt-4o")
        )
        api_key = (
            config.get("MIDSCENE_MODEL_API_KEY") or
            os.environ.get("MIDSCENE_MODEL_API_KEY") or
            os.environ.get("OPENAI_API_KEY")
        )
        base_url = (
            config.get("MIDSCENE_MODEL_BASE_URL") or
            os.environ.get("MIDSCENE_MODEL_BASE_URL") or
            os.environ.get("OPENAI_BASE_URL")
        )
        
        return {
            "model_name": model_name,
            "api_key": api_key,
            "base_url": base_url,
            "intent": intent,
            **config,
        }
    
    async def ai_tap(
        self,
        locate_prompt: TUserPrompt,
        opt: Optional[LocateOption] = None,
    ) -> Any:
        """
        Tap on an element described by natural language.
        
        Args:
            locate_prompt: Natural language description of the element
            opt: Locate options
            
        Returns:
            Action result
        """
        assert_condition(locate_prompt, "missing locate prompt for tap")
        
        detailed_locate_param = build_detailed_locate_param(locate_prompt, opt)
        
        return await self._call_action_in_action_space("Tap", {
            "locate": detailed_locate_param,
        })
    
    async def ai_double_click(
        self,
        locate_prompt: TUserPrompt,
        opt: Optional[LocateOption] = None,
    ) -> Any:
        """
        Double click on an element.
        
        Args:
            locate_prompt: Natural language description of the element
            opt: Locate options
            
        Returns:
            Action result
        """
        assert_condition(locate_prompt, "missing locate prompt for double click")
        
        detailed_locate_param = build_detailed_locate_param(locate_prompt, opt)
        
        return await self._call_action_in_action_space("DoubleClick", {
            "locate": detailed_locate_param,
        })
    
    async def ai_right_click(
        self,
        locate_prompt: TUserPrompt,
        opt: Optional[LocateOption] = None,
    ) -> Any:
        """
        Right click on an element.
        
        Args:
            locate_prompt: Natural language description of the element
            opt: Locate options
            
        Returns:
            Action result
        """
        assert_condition(locate_prompt, "missing locate prompt for right click")
        
        detailed_locate_param = build_detailed_locate_param(locate_prompt, opt)
        
        return await self._call_action_in_action_space("RightClick", {
            "locate": detailed_locate_param,
        })
    
    async def ai_hover(
        self,
        locate_prompt: TUserPrompt,
        opt: Optional[LocateOption] = None,
    ) -> Any:
        """
        Hover over an element.
        
        Args:
            locate_prompt: Natural language description of the element
            opt: Locate options
            
        Returns:
            Action result
        """
        assert_condition(locate_prompt, "missing locate prompt for hover")
        
        detailed_locate_param = build_detailed_locate_param(locate_prompt, opt)
        
        return await self._call_action_in_action_space("Hover", {
            "locate": detailed_locate_param,
        })
    
    async def ai_input(
        self,
        locate_prompt: TUserPrompt,
        opt: Dict[str, Any],
    ) -> Any:
        """
        Input text into an element.
        
        Args:
            locate_prompt: Natural language description of the element
            opt: Options including 'value' to input
            
        Returns:
            Action result
        """
        value = opt.get("value")
        assert_condition(
            isinstance(value, (str, int, float)),
            "input value must be a string or number"
        )
        assert_condition(locate_prompt, "missing locate prompt for input")
        
        detailed_locate_param = build_detailed_locate_param(
            locate_prompt,
            LocateOption(deep_think=opt.get("deep_think", False)),
        )
        
        # Convert value to string
        string_value = str(value) if not isinstance(value, str) else value
        
        return await self._call_action_in_action_space("Input", {
            "value": string_value,
            "locate": detailed_locate_param,
            "mode": opt.get("mode", "replace"),
        })
    
    async def ai_keyboard_press(
        self,
        locate_prompt: TUserPrompt,
        opt: Dict[str, Any],
    ) -> Any:
        """
        Press a keyboard key on an element.
        
        Args:
            locate_prompt: Natural language description of the element
            opt: Options including 'key_name'
            
        Returns:
            Action result
        """
        key_name = opt.get("key_name")
        assert_condition(key_name, "missing key_name for keyboard press")
        
        detailed_locate_param = None
        if locate_prompt:
            detailed_locate_param = build_detailed_locate_param(
                locate_prompt,
                LocateOption(deep_think=opt.get("deep_think", False)),
            )
        
        return await self._call_action_in_action_space("KeyboardPress", {
            "key_name": key_name,
            "locate": detailed_locate_param,
        })
    
    async def ai_scroll(
        self,
        locate_prompt: Optional[TUserPrompt],
        opt: Dict[str, Any],
    ) -> Any:
        """
        Scroll on an element or page.
        
        Args:
            locate_prompt: Optional element description to scroll within
            opt: Scroll options (direction, distance, scroll_type)
            
        Returns:
            Action result
        """
        detailed_locate_param = None
        if locate_prompt:
            detailed_locate_param = build_detailed_locate_param(
                locate_prompt,
                LocateOption(deep_think=opt.get("deep_think", False)),
            )
        
        return await self._call_action_in_action_space("Scroll", {
            "locate": detailed_locate_param,
            "direction": opt.get("direction", "down"),
            "distance": opt.get("distance"),
            "scroll_type": opt.get("scroll_type", "singleAction"),
        })
    
    async def ai_act(
        self,
        task_prompt: str,
        opt: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Perform an action described in natural language.
        
        This is the main method for AI-powered automation. The AI will
        analyze the current page state and execute the necessary steps.
        
        Args:
            task_prompt: Natural language description of what to do
            opt: Action options (cacheable, etc.)
            
        Returns:
            Action result
        """
        model_config = self._get_model_config("planning")
        
        from midscene.core.ai_model import plan_action
        
        context = await self.get_ui_context()
        
        result = await plan_action(
            context=context,
            task_prompt=task_prompt,
            model_config=model_config,
            ai_act_context=self._opts.ai_act_context,
        )
        
        if result.get("error"):
            raise Exception(f"AI action failed: {result['error']}")
        
        # Execute planned actions
        actions = result.get("actions", [])
        for action in actions:
            await self._execute_action(action)
        
        return result
    
    async def ai_query(
        self,
        demand: Union[str, Dict[str, str]],
        opt: Optional[ServiceExtractOption] = None,
    ) -> Any:
        """
        Query data from the page using natural language.
        
        Args:
            demand: Data extraction query
            opt: Extraction options
            
        Returns:
            Extracted data
        """
        model_config = self._get_model_config("insight")
        
        result = await self.service.extract(
            data_demand=demand,
            model_config=model_config,
            options=opt or ServiceExtractOption(),
        )
        
        return result.get("data")
    
    async def ai_boolean(
        self,
        prompt: TUserPrompt,
        opt: Optional[ServiceExtractOption] = None,
    ) -> bool:
        """
        Get a boolean answer from the AI.
        
        Args:
            prompt: Question to ask
            opt: Extraction options
            
        Returns:
            Boolean answer
        """
        result = await self.ai_query(
            {"answer": f"Answer with true or false: {prompt}"},
            opt,
        )
        return bool(result.get("answer"))
    
    async def ai_number(
        self,
        prompt: TUserPrompt,
        opt: Optional[ServiceExtractOption] = None,
    ) -> float:
        """
        Get a numeric answer from the AI.
        
        Args:
            prompt: Question to ask
            opt: Extraction options
            
        Returns:
            Numeric answer
        """
        result = await self.ai_query(
            {"answer": f"Answer with a number: {prompt}"},
            opt,
        )
        return float(result.get("answer", 0))
    
    async def ai_string(
        self,
        prompt: TUserPrompt,
        opt: Optional[ServiceExtractOption] = None,
    ) -> str:
        """
        Get a string answer from the AI.
        
        Args:
            prompt: Question to ask
            opt: Extraction options
            
        Returns:
            String answer
        """
        result = await self.ai_query(
            {"answer": str(prompt)},
            opt,
        )
        return str(result.get("answer", ""))
    
    async def ai_ask(
        self,
        prompt: TUserPrompt,
        opt: Optional[ServiceExtractOption] = None,
    ) -> str:
        """
        Alias for ai_string.
        
        Args:
            prompt: Question to ask
            opt: Extraction options
            
        Returns:
            String answer
        """
        return await self.ai_string(prompt, opt)
    
    async def ai_assert(
        self,
        assertion: TUserPrompt,
        msg: Optional[str] = None,
        opt: Optional[AgentAssertOpt] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Assert a condition on the page using AI.
        
        Args:
            assertion: The assertion to check
            msg: Optional custom error message
            opt: Assertion options
            
        Returns:
            Assertion result if keep_raw_response is True
            
        Raises:
            AssertionError: If assertion fails
        """
        assertion_text = assertion if isinstance(assertion, str) else str(assertion)
        
        result = await self.ai_boolean(assertion_text)
        
        if opt and opt.keep_raw_response:
            return {
                "pass": result,
                "message": None if result else f"Assertion failed: {msg or assertion_text}",
            }
        
        if not result:
            raise AssertionError(f"Assertion failed: {msg or assertion_text}")
        
        return None
    
    async def ai_wait_for(
        self,
        assertion: TUserPrompt,
        opt: Optional[AgentWaitForOpt] = None,
    ) -> None:
        """
        Wait for a condition to be true.
        
        Args:
            assertion: Condition to wait for
            opt: Wait options
        """
        import asyncio
        
        options = opt or AgentWaitForOpt()
        timeout_ms = options.timeout_ms
        check_interval_ms = options.check_interval_ms
        
        start_time = time.time() * 1000
        
        while (time.time() * 1000 - start_time) < timeout_ms:
            try:
                result = await self.ai_boolean(assertion)
                if result:
                    return
            except Exception:
                pass
            
            await asyncio.sleep(check_interval_ms / 1000)
        
        raise TimeoutError(f"Timeout waiting for: {assertion}")
    
    async def ai_locate(
        self,
        prompt: TUserPrompt,
        opt: Optional[LocateOption] = None,
    ) -> Dict[str, Any]:
        """
        Locate an element using natural language.
        
        Args:
            prompt: Description of the element to locate
            opt: Locate options
            
        Returns:
            Dict with rect and center of found element
        """
        locate_param = build_detailed_locate_param(prompt, opt)
        model_config = self._get_model_config("planning")
        
        result = await self.service.locate(
            query=locate_param,
            model_config=model_config,
        )
        
        if result.element:
            return {
                "rect": result.element.rect,
                "center": result.element.center,
            }
        
        return {"rect": None, "center": None}
    
    async def _call_action_in_action_space(
        self,
        action_type: str,
        params: Dict[str, Any],
    ) -> Any:
        """
        Call an action in the action space.
        
        Args:
            action_type: Type of action to perform
            params: Action parameters
            
        Returns:
            Action result
        """
        logger.debug("Calling action: %s with params: %s", action_type, params)
        
        action = PlanningAction(
            type=action_type,
            param=params,
            thought="",
        )
        
        return await self._execute_action(action)
    
    async def _execute_action(self, action: PlanningAction) -> Any:
        """
        Execute a planning action.
        
        Args:
            action: The action to execute
            
        Returns:
            Action result
        """
        action_type = action.type.lower()
        params = action.param
        
        # Locate element if needed
        locate_param = params.get("locate")
        element = None
        
        if locate_param:
            model_config = self._get_model_config("planning")
            result = await self.service.locate(
                query=locate_param,
                model_config=model_config,
            )
            element = result.element
            
            if element is None:
                raise Exception(f"Could not locate element: {locate_param.prompt}")
        
        # Execute action on interface
        if action_type == "tap":
            if element:
                await self.interface.mouse_click(element.center[0], element.center[1])
        elif action_type == "doubleclick":
            if element:
                await self.interface.mouse_click(
                    element.center[0], element.center[1], 
                    click_count=2
                )
        elif action_type == "rightclick":
            if element:
                await self.interface.mouse_click(
                    element.center[0], element.center[1],
                    button="right"
                )
        elif action_type == "hover":
            if element:
                await self.interface.mouse_move(element.center[0], element.center[1])
        elif action_type == "input":
            if element:
                await self.interface.mouse_click(element.center[0], element.center[1])
            await self.interface.keyboard_type(params.get("value", ""))
        elif action_type == "keyboardpress":
            await self.interface.keyboard_press(params.get("key_name", "Enter"))
        elif action_type == "scroll":
            direction = params.get("direction", "down")
            distance = params.get("distance", 300)
            x, y = element.center if element else (0, 0)
            await self.interface.mouse_wheel(x, y, 0, distance if direction == "down" else -distance)
        
        return {"success": True}
    
    async def run_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """
        Run a YAML automation script.
        
        Args:
            yaml_content: YAML script content
            
        Returns:
            Execution result
        """
        from midscene.core.yaml import parse_yaml_script, ScriptPlayer
        
        script = parse_yaml_script(yaml_content)
        
        async def agent_factory():
            return {"agent": self, "free_fn": []}
        
        player = ScriptPlayer(script, agent_factory)
        await player.run()
        
        if player.status == "error":
            errors = [
                f"task - {task['name']}: {task.get('error', {}).get('message', 'Unknown error')}"
                for task in player.task_status_list
                if task.get("status") == "error"
            ]
            raise Exception(f"Error(s) in YAML script:\n" + "\n".join(errors))
        
        return {"result": player.result}
    
    async def freeze_page_context(self) -> None:
        """Freeze the current page context for batch operations."""
        logger.debug("Freezing page context")
        context = await self.get_ui_context()
        context.is_frozen = True
        self._frozen_ui_context = context
        logger.debug("Page context frozen successfully")
    
    async def unfreeze_page_context(self) -> None:
        """Unfreeze the page context."""
        logger.debug("Unfreezing page context")
        self._frozen_ui_context = None
        logger.debug("Page context unfrozen successfully")
    
    async def destroy(self) -> None:
        """Destroy the agent and release resources."""
        if self._destroyed:
            return
        
        if hasattr(self.interface, "destroy"):
            await self.interface.destroy()
        
        self._dump = self._reset_dump()
        self._destroyed = True
    
    def add_dump_update_listener(
        self,
        listener: Callable[[str, Optional[ExecutionDump]], None],
    ) -> Callable[[], None]:
        """
        Add a dump update listener.
        
        Args:
            listener: Listener function
            
        Returns:
            Function to remove the listener
        """
        self._dump_update_listeners.append(listener)
        
        def remove():
            if listener in self._dump_update_listeners:
                self._dump_update_listeners.remove(listener)
        
        return remove
    
    # Aliases for backward compatibility
    async def ai_action(self, *args, **kwargs):
        """Deprecated: use ai_act instead."""
        return await self.ai_act(*args, **kwargs)
    
    async def set_ai_action_context(self, prompt: str) -> None:
        """Deprecated: use set_ai_act_context instead."""
        await self.set_ai_act_context(prompt)
    
    async def set_ai_act_context(self, prompt: str) -> None:
        """Set the AI action context."""
        if self._opts.ai_act_context:
            logger.warning("ai_act_context is already set, overriding")
        self._opts.ai_act_context = prompt
