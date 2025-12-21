import logging
import os
from datetime import datetime
from google.genai import types
import json 

logger = logging.getLogger(__name__)

def create_list_of_prompts(user_prompt: str,  client, chat_model: str, prompt_prefix: str = "", prompt_suffix: str = "",  max_tries: int = 3, num_prompts: int = 1) -> list[str]:
    """
    Creates a list with num_prompts many prompts based on user input.
    """
    response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "STRING"
        }
    }
    try:
        final_prompt = f"{prompt_prefix}\n{user_prompt}\n{prompt_suffix} {num_prompts}"
        logger.info(f"Final create list of prompts prompt: {final_prompt}")
        for i in range(1, max_tries + 1):
                print(f"Crating the list of prompts, try {i} / {max_tries} ...")
                prompts = client.models.generate_content(
                    model=chat_model,
                    contents=final_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema
                        )
                    ).text
                prompts = json.loads(prompts)
                if len(prompts) == num_prompts:
                    logger.info(f"Created {len(prompts)} prompts on {i}. try.")
                    return prompts
        logger.error(f"Error: The AI is not able to create the required number of prompts. Created number of prompts: {len(prompts)}: required: {num_prompts} \n output of AI: {prompts, type(prompts)}")
        return prompts
    except Exception as e:
        logger.error(f"Error creating prompts: {e}")
        return ['error occurec']   
    

def optimize_image_prompts(user_prompts: list, user_image_style_description: str, client, chat_model: str, prompt_prefix: str = "", prompt_suffix: str = "") -> list[str]:
    """
    Makes a single AI call for each user_prompt to optimize the prompts:  This should achieve better results than optimizing all prompts in a single call.
    The AI behaviour can be optimized with the prompt prefix and suffix.
    """
    outputs = []
    response_schema = {
        "type": "STRING"
    }
    try:
        for i, user_prompt in enumerate(user_prompts, 1):
            print(f"Optimizing prompt {i}/{len(user_prompts)}...")
            final_prompt = f"{prompt_prefix}\n{user_image_style_description}\n Given the aforementioned requirements please now create a prompt to generate an image showing the following scene: \n {user_prompt}\n{prompt_suffix}"
            logger.info(f"Final optimize image prompt: {final_prompt}")
            output = client.models.generate_content(
                model=chat_model,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema
                    )
                ).text
            outputs.append(json.loads(output))
        if logger.isEnabledFor(logging.INFO):
            logger.info("Input user prompt -> Output:")
            for input_user_prompt, output in zip(user_prompts, outputs):
                logger.info(f"{input_user_prompt} ->  {output}")
        return outputs
    except Exception as e:
        logger.error(f"Error optimizing prompts: {e}")
        return []

def generate_and_save_images(prompts: list[str],
                            client, 
                            image_model: str, 
                            prompt_prefix: str = "",
                            prompt_suffix: str = "",
                            num_images: int = 1, 
                            output_folder: str = "generated_images"
                            ) -> bool:
    """
    Generates an image from a prompt and returns the result in a specific format.
    """
    n = len(prompts)
    try:
        # Ensure output directory exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        image_progress = 1
        for prompt in prompts:
            print(f"Generating {num_images} images for prompt: {image_progress}/{n}")
            logger.info(f"Generating {num_images} images for prompt: {image_progress}/{n}")
            final_prompt = prompt_prefix + prompt + prompt_suffix
            logger.info(f"Final image generation prompt: {final_prompt}")
            response = client.models.generate_images(
                model=image_model,
                prompt=final_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=num_images,
                )
            )
            if response.generated_images:
                for i in range(len(response.generated_images)):
                    generated_image = response.generated_images[i].image
                    
                    # Create a filename based on timestamp and prompt
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"image-{image_progress}-version-{i}-{timestamp}.png"
                    file_path = os.path.join(output_folder, filename)
                    generated_image.save(file_path)
                    logger.info(f"Saved generated image to {file_path}")
            else:
                logger.warning("No image generated")
            image_progress += 1
        return True
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False
    
def create_descriptions(optimized_image_generation_prompts: list[str], 
                        user_image_desription_description: str, 
                        language: str, client, 
                        chat_model: str, 
                        prompt_prefix: str = "", 
                        prompt_suffix: str = ""):
    """
    Makes a single AI call for each user_prompt to optimize the prompts:  This should achieve better results than optimizing all prompts in a single call.
    The AI behaviour can be optimized with the prompt prefix and suffix.
    """
    outputs = []
    response_schema = {
        "type": "STRING"
    }
    try:
        for prompt in optimized_image_generation_prompts:
            final_prompt = f"{prompt_prefix}\n{user_image_desription_description}\n Write a descrription for the following image creation prompt: \n {prompt}\n{prompt_suffix} {language}"
            logger.info(f"Final create description prompt: {final_prompt}")
            output = client.models.generate_content(
                model=chat_model,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema
                        )
            ).text
            outputs.append(json.loads(output))
        if logger.isEnabledFor(logging.INFO):
            logger.info("prompt -> description:")
            for prompt, description in zip(optimized_image_generation_prompts, outputs):
                logger.info(f"{prompt} ->  {description}")
        return outputs
    except Exception as e:
        logger.error(f"Error optimizing prompts: {e}")
        return []